"""Validate candidate identity and transformation metadata after pinned-source preflight."""
from pathlib import Path
import json
from replay_config import config
CFG=config();O=Path(CFG['output_dir'])
P=Path(CFG['ambiqt_root']);results=[]
for cat,outcat,fields in [('col-synonyms','col-synonyms',['extra_map','query1','query2']),('tbl-synonyms','table-synonyms',['extra_table_map','query1','query2']),('tbl-split','join-ambiguity',['split_map','primary_key','query1','query2']),('tbl-agg','precomputed-aggregates',['new_table_name','query1','query2'])]:
 v=json.loads((P/cat/'validation.json').read_text())
 for model in ['logical-beam','t5-3b-bw10']:
  rr=json.loads((P/f'outputs/{outcat}/{model}.json').read_text());assert len(v)==len(rr)
  bad={k:[i for i,(a,b) in enumerate(zip(rr,v)) if a.get(k)!=b.get(k)] for k in fields};results.append({'category':cat,'model':model,'mismatches':bad})
  assert all(not bad[k] for k in fields if k not in ['query1','query2'])
  for key,ids in bad.items():
   if ids:assert cat=='tbl-agg' and model=='t5-3b-bw10' and key=='query2' and ids==[44,73,74,75,76,77,78]
(O/'ambiqt_transform_identity_validation.json').write_text(json.dumps(results,indent=2)+'\n')
print('Transformation maps match. Seven recorded unused query2 discrepancies retained.')
