"""Cross-check wrapper against native evaluate_all on deterministic subsets."""
from pathlib import Path
import sys,os,json,importlib.util,sqlite3,io,contextlib,re,time
from replay_config import config
CFG=config();S=Path(CFG['ambiqt_root']);O=Path(CFG['output_dir']);os.environ['NLTK_DATA']=CFG['nltk_data']
def load(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
orig=sqlite3.connect
def ro(db,*a,**kw):
 con=orig('file:'+str(Path(db).resolve())+'?mode=ro',uri=True);end=time.monotonic()+5;con.set_progress_handler(lambda:int(time.monotonic()>end),10000);return con
sqlite3.connect=ro
checks=[]
for cat,outcat in [('col-synonyms','col-synonyms'),('tbl-synonyms','table-synonyms'),('tbl-split','join-ambiguity'),('tbl-agg','precomputed-aggregates')]:
 load('process_sql',S/cat/'process_sql.py');ev=load('native_validation_'+cat.replace('-','_'),S/cat/'evaluate.py');ev.DB_DIR=str(S/'db-content/database');ev.TABLE_PATH=str(S/'tables.json')
 data=json.loads((S/f'outputs/{outcat}/logical-beam.json').read_text());records=[json.loads(x) for x in (O/f'ambiqt_{cat}_logical-beam_records.jsonl').read_text().splitlines()]
 ids=sorted(set(list(range(min(20,len(records))))+[r['index'] for r in records if not r['gold_status']['execute_ok']]))
 temp=O/f'native-validation-sample-{cat}.json';temp.write_text(json.dumps([data[i] for i in ids]))
 for k in [1,5,10]:
  buf=io.StringIO()
  with contextlib.redirect_stdout(buf),contextlib.redirect_stderr(io.StringIO()):ev.evaluate_all(str(temp),k=k)
  txt=buf.getvalue();(O/f'native_check_{cat}_k{k}.log').write_text(txt)
  for outcome in ['either','both']:
   sec=txt.split(f'Accuracy of having *{outcome}*')[1]
   for metric,label in [('exact','Exact Set Match Accuracy'),('native_exec','Execution Match Accuracy'),('direct_exec','Direct Execution Match (non-test-suite) Accuracy')]:
    match=re.search(re.escape(label)+r'\s*=\s*([0-9.]+)%',sec);published=float(match.group(1));hits=0
    for i in ids:
     scores=records[i]['candidate_scores'][:k];flags=[any(s['alternatives'][a][metric]==1 for s in scores) for a in [0,1]];hits+=any(flags) if outcome=='either' else all(flags)
    our=100*hits/len(ids);checks.append({'category':cat,'budget':k,'outcome':outcome,'metric':metric,'N':len(ids),'wrapper_pct':our,'native_printed_pct':published,'pass':abs(our-published)<=.00500001})
(O/'ambiqt_native_replay_validation.json').write_text(json.dumps(checks,indent=2)+'\n')
print('checks',len(checks),'passed',sum(x['pass'] for x in checks));assert all(x['pass'] for x in checks)
