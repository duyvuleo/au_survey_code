"""Audit SQLite source-table population without modifying references/outcomes."""
from pathlib import Path
import csv,json,time
from run_experiment import OUT,SCHEMAS,CONNS,schema,connection,arm_timeout,quote,parse,exp

rows=[json.loads(s) for s in (OUT/'bundle-ledger.jsonl').read_text().splitlines()]
tables={}
for ds,db in sorted({(r['dataset'],r['db_id']) for r in rows}):
 try:sch=schema(ds,db)
 except Exception as e:continue
 c=connection(ds,db)
 for t,info in sch.items():
  if t.startswith('sqlite_'):continue
  arm_timeout(c)
  try:n=c.execute('SELECT COUNT(*) FROM '+quote(info['name'])).fetchone()[0];v={'ok':True,'row_count':n}
  except Exception as e:v={'ok':False,'error':type(e).__name__+': '+str(e)}
  tables[ds,db,t]={'dataset':ds,'db_id':db,'table':info['name'],**v}
for r in rows:
 try:
  a=parse(r['parent_sql']);sch=schema(r['dataset'],r['db_id'])
  used=sorted({t.name.lower() for t in a.find_all(exp.Table) if t.name.lower() in sch and not t.name.lower().startswith('sqlite_')})
  pp=[tables[r['dataset'],r['db_id'],t] for t in used if (r['dataset'],r['db_id'],t) in tables]
  r['source_relation_population']=pp
  r['references_empty_source_relation']=any(x.get('ok') and x['row_count']==0 for x in pp)
  r['all_identified_source_relations_nonempty']=bool(pp) and all(x.get('ok') and x['row_count']>0 for x in pp) and len(pp)==len(used)
 except Exception as e:
  r['source_relation_population_unresolved']=type(e).__name__+': '+str(e);r['all_identified_source_relations_nonempty']=False
(OUT/'bundle-ledger.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
(OUT/'source-table-population.json').write_text(json.dumps(list(tables.values()),indent=2)+'\n')
with (OUT/'source-table-population.csv').open('w',newline='') as f:
 keys=['dataset','db_id','table','ok','row_count','error'];w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(tables.values())
receipt={'tables_inspected':len(tables),'successful_counts':sum(v['ok'] for v in tables.values()),'empty_tables':[v for v in tables.values() if v.get('ok') and v['row_count']==0],'method':'Exact COUNT(*) on read-only pinned source tables; neither SQL references nor result signatures changed. All-identified-source-relations-nonempty is a descriptive sensitivity, not annotation validation.'}
(OUT/'population-audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Table census',len(tables),'empty',len(receipt['empty_tables']),flush=True)
for c in CONNS.values():c.close()
