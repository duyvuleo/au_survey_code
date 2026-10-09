"""Feed every released gold SQL back through unchanged native metrics (not model output)."""
from pathlib import Path
from collections import Counter
import csv,json,sqlite3,importlib.util,sys,time
from replay_config import config
CFG=config();OUT=Path(CFG['output_dir']);csv.field_size_limit(10000000)
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
load('exceptions',Path(CFG['ambrosia_exceptions']));metric=load('ambrosia_metrics',Path(CFG['ambrosia_metrics']))
orig=sqlite3.connect
def readonly(database,*a,**kw):
 con=orig('file:'+str(Path(database).resolve())+'?mode=ro',uri=True);end=time.monotonic()+5;con.set_progress_handler(lambda:int(time.monotonic()>end),10000);return con
sqlite3.connect=readonly
rows=list(csv.DictReader((Path(CFG['ambrosia_data_root'])/'data/ambrosia.csv').open(newline='')));out=[]
rows=[r for r in rows if r['is_ambiguous']=='True' and (not CFG['record_ids'] or r[''] in CFG['record_ids'])]
rows=rows[:CFG['limit']] if CFG['limit'] else rows
for r in rows:
 if r['is_ambiguous']!='True':continue
 q=r['gold_queries'].split('\n\n');db=Path(CFG['ambrosia_data_root'])/r['db_file']
 d={'record_id':r[''],'split':r['split'],'ambig_type':r['ambig_type'],'gold_list_count':len(q),'gold_unique_sql_count':len(set(q))}
 try:d.update(metric.evaluate_predicted_statements(str(db),q,q))
 except Exception as e:d['error']=type(e).__name__+': '+str(e)
 out.append(d)
(OUT/'ambrosia_gold_oracle.json').write_text(json.dumps(out,indent=2)+'\n')
summary={}
for split in ['all','test','few_shot_examples']:
 sub=[x for x in out if split=='all' or x['split']==split];ok=[x for x in sub if 'error' not in x]
 summary[split]={'N':len(sub),'evaluated':len(ok),'errors':len(sub)-len(ok),'mean_recall':sum(x['recall'] for x in ok)/len(ok) if ok else None,'mean_precision':sum(x['precision'] for x in ok)/len(ok) if ok else None,'all_found_count':sum(x['all_found'] for x in ok),'nonperfect':[x for x in ok if x['recall']!=1 or not x['all_found']]}
(OUT/'ambrosia_gold_oracle_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
