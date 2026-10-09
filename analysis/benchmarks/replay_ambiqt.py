"""Replay saved candidate prefixes with pinned native AmbiQT functions.
No inference. Separate exact/parser, native exec and direct exec comparators.
Invoke through replay.py ambiqt.
"""
from pathlib import Path
from collections import Counter
import sys,os,json,csv,sqlite3,importlib.util,time,hashlib
from replay_config import config
CFG=config();SRC=Path(CFG['ambiqt_root']);OUT=Path(CFG['output_dir'])
os.environ['NLTK_DATA']=CFG['nltk_data']
CATS={'col-synonyms':'col-synonyms','tbl-synonyms':'table-synonyms','tbl-split':'join-ambiguity','tbl-agg':'precomputed-aggregates'}
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
# Read-only SQLite: generated candidates cannot mutate downloaded benchmark databases.
original_connect=sqlite3.connect
class ReadonlyConnection(sqlite3.Connection):
 pass
def readonly_connect(database,*a,**kw):
 database=str(database)
 if not database.startswith('file:'):database='file:'+str(Path(database).resolve())+'?mode=ro'
 kw['uri']=True
 con=original_connect(database,*a,**kw);deadline=time.monotonic()+5
 con.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
 return con
sqlite3.connect=readonly_connect
for cat in CFG['categories']:
 load('process_sql',SRC/cat/'process_sql.py');ev=load('native_'+cat.replace('-','_'),SRC/cat/'evaluate.py')
 ev.DB_DIR=str(SRC/'db-content/database');ev.TABLE_PATH=str(SRC/'tables.json');ev.EVALUATOR=ev.Evaluator();ev.KMAPS=ev.build_foreign_key_map_from_json(ev.TABLE_PATH)
 ev.DB_MAP={k:x.name for x in Path(ev.DB_DIR).iterdir() if x.is_dir() for k in [x.name,x.name.lower()]}
 validation=json.loads((SRC/cat/'validation.json').read_text());summaries=[];artifact=[]
 for model in ['logical-beam','t5-3b-bw10']:
  path=SRC/'outputs'/CATS[cat]/(model+'.json');rows=json.loads(path.read_text());rows=rows[:CFG['limit']] if CFG['limit'] else rows;records=[];mismatch=[];goldfail=[];errors=Counter();cache={}
  for ix,r in enumerate(rows):
   if ix>=len(validation) or any(r.get(k)!=validation[ix].get(k) for k in ['db_id','question','orig_query']):mismatch.append(ix)
   pk='t2s_outs' if 't2s_outs' in r else 'template_filled';pool=ev.get_selections(r[pk],k=10)[:10]
   db=r['db_id'];gold=ev.normalize_sql(r['orig_query']);dbpath=Path(ev.DB_DIR)/db/(db+'.sqlite')
   gstatus={};schema=None
   try:
    schema=ev.Schema(ev.get_schema(str(dbpath)));ev.get_sql(schema,gold);gstatus['parse_ok']=True
   except Exception as e:gstatus['parse_ok']=False;gstatus['parse_error']=str(e)
   try:
    conn=sqlite3.connect(dbpath);gout=conn.execute(gold).fetchall();conn.close();gstatus.update({'execute_ok':True,'rows':len(gout),'empty':not bool(gout)})
   except Exception as e:gstatus.update({'execute_ok':False,'execute_error':str(e)})
   rec={'category':cat,'model':model,'index':ix,'db_id':db,'orig_example_idx':r.get('orig_example_idx'),'question_sha256':hashlib.sha256(r['question'].encode()).hexdigest(),'pool_count':len(pool),'gold_status':gstatus,'candidate_scores':[]}
   if not gstatus.get('parse_ok') or not gstatus.get('execute_ok'):goldfail.append(ix)
   for rank,p in enumerate(pool,1):
    if cat in ['col-synonyms','tbl-synonyms']:
     fm=ev.flatten_map(r['extra_map']) if cat=='col-synonyms' else r['extra_table_map']
     ps=[ev.get_modified_sql_for_alt_eval(p,fm,alt_num=i) for i in [0,1]]
    else:
     if '@' in p:p=p[p.rfind('@')+1:].strip()
     ps=[p,ev.get_modified_sql_for_alt_eval(p,r['split_map'],r['primary_key']) if cat=='tbl-split' else ev.get_modified_sql(p,gold,r['new_table_name'])]
    res=[]
    for pp in ps:
     if '@' in pp:pp=pp[pp.rfind('@')+1:].strip()
     key=(db,gold,pp)
     if key not in cache:
      try:
       em,ex=ev.evaluate_wrt_gold(pp,gold,db,also_return_exec=True);direct=ev.direct_execution_match(pp,gold,db)
       cache[key]={'exact':em,'native_exec':ex,'direct_exec':direct}
      except Exception as e:
       errors[type(e).__name__+': '+str(e)]+=1;cache[key]={'exact':None,'native_exec':None,'direct_exec':None,'error':str(e)}
     res.append(dict(cache[key]))
    # Native split/aggregate evaluator assigns a candidate to alternative only
    # when it was not already correct for original, separately by comparator.
    if cat in ['tbl-split','tbl-agg']:
     for metric in ['exact','native_exec','direct_exec']:
      if res[0][metric] is not None and res[1][metric] is not None:res[1][metric]*=1-res[0][metric]
    rec['candidate_scores'].append({'rank':rank,'sql_sha256':hashlib.sha256(p.encode()).hexdigest(),'alternatives':res})
   records.append(rec)
   if (ix+1)%100==0:print(cat,model,ix+1,'/',len(rows),flush=True)
  (OUT/f'ambiqt_{cat}_{model}_records.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in records))
  artifact.append({'category':cat,'model':model,'source_records':len(rows),'validation_records':len(validation),'mismatched_identity_indices':mismatch,'gold_failed_indices':goldfail,'pool_size_distribution':dict(Counter(r['pool_count'] for r in records)),'unique_source_question_strings':len(set(r['question'] for r in rows)),'unique_databases':len(set(r['db_id'] for r in rows)),'caught_evaluator_exceptions':dict(errors),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
  for budget in [1,2,3,5,10]:
   for metric in ['exact','native_exec','direct_exec']:
    for guard in ['native_all','gold_valid_only']:
     eligible=[r for r in records if guard=='native_all' or (r['gold_status'].get('parse_ok') and r['gold_status'].get('execute_ok'))]
     either=both=0;unresolved=short=0
     for r in eligible:
      scores=r['candidate_scores'][:budget];short+=r['pool_count']<budget
      flags=[any(s['alternatives'][a].get(metric)==1 for s in scores) for a in [0,1]]
      # No evaluator exception is silently counted as a validated negative.
      unresolved+=any(s['alternatives'][a].get(metric) is None for s in scores for a in [0,1])
      either+=any(flags);both+=all(flags)
     summaries.append({'category':cat,'model':model,'budget':budget,'comparator':metric,'population':guard,'N':len(eligible),'either_count':either,'both_count':both,'either_rate':either/len(eligible),'both_rate':both/len(eligible),'unresolved_requests':unresolved,'short_candidate_pools':short})
  print('DONE',cat,model,artifact[-1],flush=True)
 with (OUT/f'ambiqt_{cat}_summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
 (OUT/f'ambiqt_{cat}_artifact_audit.json').write_text(json.dumps(artifact,indent=2)+'\n')
