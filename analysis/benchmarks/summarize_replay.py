from pathlib import Path
from collections import Counter
import json,csv
from replay_config import config
CFG=config();O=Path(CFG['output_dir']);allrows=[];matched=[];fixed=[];audit=[]
for cat in ['col-synonyms','tbl-synonyms','tbl-split','tbl-agg']:
 models=['logical-beam','t5-3b-bw10'];rs={m:[json.loads(x) for x in (O/f'ambiqt_{cat}_{m}_records.jsonl').read_text().splitlines()] for m in models}
 assert len(rs[models[0]])==len(rs[models[1]])
 allrows.extend(list(csv.DictReader((O/f'ambiqt_{cat}_summary.csv').open())))
 audit.extend(json.loads((O/f'ambiqt_{cat}_artifact_audit.json').read_text()))
 for k in [1,2,3,5,10]:
  ids=[i for i in range(len(rs[models[0]])) if all(rs[m][i]['pool_count']>=k and rs[m][i]['gold_status'].get('parse_ok') and rs[m][i]['gold_status'].get('execute_ok') for m in models)]
  for m in models:
   for comp in ['exact','native_exec','direct_exec']:
    either=both=unresolved=0
    for i in ids:
     scores=rs[m][i]['candidate_scores'][:k];flags=[any(s['alternatives'][a][comp]==1 for s in scores) for a in [0,1]];either+=any(flags);both+=all(flags)
     unresolved+=any(s['alternatives'][a][comp] is None for s in scores for a in [0,1])
    matched.append({'category':cat,'model':m,'budget':k,'comparator':comp,'population':'same_records_both_models_supply_full_k_and_gold_valid','N':len(ids),'either_count':either,'both_count':both,'either_rate':either/len(ids),'both_rate':both/len(ids),'unresolved_requests':unresolved,'excluded_from_source_N':len(rs[m])-len(ids)})
for name,rows in [('ambiqt_all_summary.csv',allrows),('ambiqt_matched_full_budget.csv',matched)]:
 with (O/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(O/'ambiqt_artifact_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('Replay source records',sum(x['source_records'] for x in audit),'summary rows',len(allrows),'strict matched rows',len(matched))
for r in matched:
 if r['budget'] in [1,10] and r['comparator']=='native_exec':print(r)

# Fixed common full-10 population isolates prefix-budget effects without population drift.
for cat in ['col-synonyms','tbl-synonyms','tbl-split','tbl-agg']:
 models=['logical-beam','t5-3b-bw10'];rs={m:[json.loads(x) for x in (O/f'ambiqt_{cat}_{m}_records.jsonl').read_text().splitlines()] for m in models}
 ids=[i for i in range(len(rs[models[0]])) if all(rs[m][i]['pool_count']>=10 and rs[m][i]['gold_status'].get('parse_ok') and rs[m][i]['gold_status'].get('execute_ok') for m in models)]
 for k in [1,2,3,5,10]:
  for m in models:
   for comp in ['exact','native_exec','direct_exec']:
    ei=bo=0
    for i in ids:
     sc=rs[m][i]['candidate_scores'][:k];fl=[any(z['alternatives'][a][comp]==1 for z in sc) for a in [0,1]];ei+=any(fl);bo+=all(fl)
    fixed.append({'category':cat,'model':m,'budget':k,'comparator':comp,'N':len(ids),'either_count':ei,'both_count':bo,'either_rate':ei/len(ids),'both_rate':bo/len(ids),'population':'fixed_common_full10_gold_valid'})
with (O/'ambiqt_fixed_common_population.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(fixed[0]));w.writeheader();w.writerows(fixed)
