"""Run gold-to-gold comparator audit on AMBROSIA. No model inference.
Retains all requested gold fields, positions and duplicates. External data are read-only.
"""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import csv,json,hashlib,sqlite3,importlib.util,sys,time
from replay_config import config
CFG=config();OUT=Path(CFG['output_dir']);ARCHIVE=Path(CFG['ambrosia_archive']) if CFG.get('ambrosia_archive') else None;DATA=Path(CFG['ambrosia_data_root'])/'data'
csv.field_size_limit(10000000)
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
load('exceptions',Path(CFG['ambrosia_exceptions']));metric=load('ambrosia_metrics',Path(CFG['ambrosia_metrics']))
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
rows=list(csv.DictReader((DATA/'ambrosia.csv').open(newline='')));selected=[r for r in rows if r['is_ambiguous'].lower()=='true']
print('CSV records',len(rows),'ambiguous records',len(selected), 'flags',Counter(r['is_ambiguous'] for r in rows))
if not selected:selected=[r for r in rows if r['question_type']=='ambig']
full_selected_count=len(selected)
selected=[r for r in selected if not CFG['record_ids'] or r[''] in CFG['record_ids']]
selected=selected[:CFG['limit']] if CFG['limit'] else selected
records=[];pairs=[];cases=[];group=defaultdict(Counter)
for r in selected:
 rid=r[''];key=(r['split'],r['ambig_type']);g=group[key];g['requests']+=1
 rel=r['db_file'];db=Path(CFG['ambrosia_data_root'])/rel
 if not db.exists():db=DATA/rel.removeprefix('data/')
 queries=r['gold_queries'].split('\n\n')
 rec={'record_id':rid,'split':r['split'],'ambig_type':r['ambig_type'],'db_file':rel,'database_available':db.exists(),'question_sha256':digest(r['question']),'gold_count':len(queries),'attachment_instruction_retained':r['ambig_type']=='attachment','query_sha256':[digest(x) for x in queries],'gold_executions':[]}
 g['gold_queries']+=len(queries)
 if not db.exists():g['missing_database']+=1;records.append(rec);continue
 con=sqlite3.connect(f'file:{db.resolve()}?mode=ro',uri=True);results=[];cols=[]
 for q in queries:
  deadline=time.monotonic()+5;con.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
  try:
   cur=con.execute(q);c=[x[0] for x in cur.description];a=cur.fetchall();results.append(a);cols.append(c)
   rec['gold_executions'].append({'ok':True,'row_count':len(a),'column_count':len(c),'columns':c,'result_sha256':digest(a)})
   g['executed_gold']+=1;g['empty_gold']+=not bool(a)
  except Exception as e:
   results.append(None);cols.append(None);rec['gold_executions'].append({'ok':False,'error':str(e)});g['failed_gold']+=1
 con.close();rec['all_gold_executed']=all(x is not None for x in results);rec['all_gold_nonempty']=all(bool(x) for x in results)
 if rec['all_gold_executed']:g['all_gold_executed_requests']+=1
 anyflags=Counter()
 for i,j in combinations(range(len(queries)),2):
  a,b=results[i],results[j]
  if a is None or b is None:continue
  exact=a==b;bag=Counter(a)==Counter(b);st=set(a)==set(b);samewidth=(len(cols[i])==len(cols[j]));nonempty=bool(a) and bool(b)
  # Native is directional: ordering depends on the target gold query.
  ab=metric.compare_query_results(a,b,order_by='order by' in queries[j].lower())
  ba=metric.compare_query_results(b,a,order_by='order by' in queries[i].lower())
  ob_i='order by' in queries[i].lower();ob_j='order by' in queries[j].lower()
  structural=exact if ob_i or ob_j else bag
  pair={'record_id':rid,'split':r['split'],'ambig_type':r['ambig_type'],'gold_i':i,'gold_j':j,'nonempty':nonempty,'same_width':samewidth,'exact_list_match':exact,'row_bag_match':bag,'row_set_match':st,'order_sensitive_row_match':structural,'native_i_to_j':ab,'native_j_to_i':ba,'native_direction_differs':ab!=ba,'native_match_without_row_bag_match':(ab or ba) and not bag,'native_match_without_order_sensitive_rows':(ab or ba) and not structural,'source_i_has_order_by':ob_i,'source_j_has_order_by':ob_j}
  pairs.append(pair);g['gold_pairs']+=1
  for k in ['exact_list_match','row_bag_match','row_set_match','order_sensitive_row_match','native_i_to_j','native_j_to_i','native_direction_differs','native_match_without_row_bag_match','native_match_without_order_sensitive_rows']:
   g[k]+=int(pair[k]);anyflags[k]=max(anyflags[k],int(pair[k]))
  if (ab or ba) or bag:
   cases.append({'record_id':rid,'question':r['question']+(' Show them in one table.' if r['ambig_type']=='attachment' else ''),'db_file':rel,'query_i':queries[i],'query_j':queries[j],'columns_i':cols[i],'columns_j':cols[j],'result_i':a,'result_j':b,'comparison':pair})
 for k,v in anyflags.items():g['requests_with_'+k]+=v
 records.append(rec)
summary={'archive_sha256':hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() if ARCHIVE else 'not_supplied_extracted_files_hash_checked','all_csv_records':len(rows),'ambiguous_requests':len(selected),'unambiguous_rows_not_counted_as_requests':len(rows)-full_selected_count,'distinct_ambiguous_databases':len(set(r['db_file'] for r in selected)),'strata':[{'split':s,'ambig_type':t,**dict(c)} for (s,t),c in sorted(group.items())],'totals':dict(sum(group.values(),Counter())),'method':'all gold columns retained; positions retained in row comparators; native comparator loaded unchanged; directed native ordering; SQL executed read-only; no inference','semantic_validation':'Reference executability and result structure audited; source-question semantic faithfulness requires separate manual inspection. No coarser task projection.'}
(OUT/'ambrosia_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(OUT/'ambrosia_records.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
with (OUT/'ambrosia_pair_comparisons.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
# Raw question, SQL and result previews are not emitted by this adapter.
# Mechanistic probes are explicitly synthetic and not corpus observations.
probes=[]
for name,a,b,ordered in [('row_association',[(1,2),(3,4)],[(1,3),(2,4)],False),('column_position',[(1,2)],[(2,1)],False),('shape',[(1,2)],[(1,),(2,)],False),('ordered_column_position',[(1,2),(3,4)],[(2,1),(4,3)],True),('empty',[],[],False)]:
 probes.append({'case':name,'native':metric.compare_query_results(a,b,ordered),'row_bag_equal':Counter(a)==Counter(b),'origin':'synthetic comparator test; not a benchmark record'})
(OUT/'ambrosia_synthetic_comparator_tests.json').write_text(json.dumps(probes,indent=2)+'\n')
print(json.dumps(summary,indent=2))
