"""Compute explicit denominators and sensitivities from the final saved census."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,json

from replay_config import output_dir, semantic_review_path
HERE=Path(__file__).resolve().parent;O=output_dir()
rows=[json.loads(s) for s in (O/'bundle-ledger.jsonl').read_text().splitlines()]
def measure(rr):
 complete=[r for r in rr if r.get('all_alternatives_executed')]
 return {'N':len(rr),'conversation_records':sum(r['conversation_records'] for r in rr),'complete_reference_sets':len(complete),'unanimous_agreement':sum(r.get('all_alternatives_agree') is True for r in rr),'any_pair_agreement':sum(r.get('any_pair_agrees') is True for r in rr),
         'unanimous_rate':sum(r.get('all_alternatives_agree') is True for r in rr)/len(rr) if rr else None,
         'all_empty_agreements':sum(r.get('all_alternatives_agree') is True and r.get('all_empty') for r in rr),
         'all_null_agreements':sum(r.get('all_alternatives_agree') is True and r.get('all_null') for r in rr),
         'scalar_zero_agreements':sum(r.get('all_alternatives_agree') is True and r.get('all_scalar_zero') for r in rr),
         'empty_source_relation_agreements':sum(r.get('all_alternatives_agree') is True and r.get('references_empty_source_relation') for r in rr),
         'executed_query_instances':sum(sum(v['execution']['ok'] for v in r.get('references',[])) for r in rr),'failed_reference_instances':sum(r.get('reference_failures',0) for r in rr)}
summary={};flat=[];exclusions=[]
for ds in ['spider','bird']:
 rr=[r for r in rows if r['dataset']==ds]
 complete=[r for r in rr if r.get('all_alternatives_executed')]
 column=[r for r in complete if not r['category'].startswith('value')]
 primary=[r for r in rr if r.get('fixed_output_screened_eligible')]
 populations={'complete_execution_diagnostic':complete,'complete_column_execution_diagnostic':column,'fixed_output_screened':primary,
              'fixed_output_nonempty_results':[r for r in primary if not r.get('all_empty')],
              'fixed_output_nonempty_source_relations':[r for r in primary if r.get('all_identified_source_relations_nonempty')],
              'fixed_output_nonempty_source_and_results':[r for r in primary if r.get('all_identified_source_relations_nonempty') and not r.get('all_empty')],
              'fixed_output_nonnull_nonempty_results':[r for r in primary if not r.get('all_empty') and not r.get('all_null')]}
 populations['fixed_output_single_target_occurrence']=[r for r in primary if all(len(t['spans'])==1 for t in r['targets'])]
 populations['fixed_output_single_occurrence_nonempty_source']=[r for r in populations['fixed_output_single_target_occurrence'] if r.get('all_identified_source_relations_nonempty')]
 summary[ds]={'intake_bundles':len(rr),'category_bundles':dict(Counter(r['category'] for r in rr)),'status_counts':dict(Counter(r['status'] for r in rr)),
              'construction_unresolved_reasons':dict(Counter(r.get('construction_reason') for r in rr if r['status']=='construction_unresolved')),'populations':{name:measure(p) for name,p in populations.items()}}
 for name,pop in populations.items():
  flat.append({'dataset':ds,'category':'all','population':name,**measure(pop)})
  for cat in sorted({r['category'] for r in rr}):flat.append({'dataset':ds,'category':cat,'population':name,**measure([r for r in pop if r['category']==cat])})
 for reason,n in Counter(x for r in rr for x in r.get('fixed_output_exclusion_reasons',[r.get('construction_reason',r['status'])]) if not r.get('fixed_output_screened_eligible')).items():
  exclusions.append({'dataset':ds,'reason':reason,'bundle_count':n,'count_unit':'overlapping exclusion reasons; cannot sum as unique excluded cases'})
 # Database counts retain small denominators rather than ranking them.
 for db in sorted({r['db_id'] for r in primary}):flat.append({'dataset':ds,'category':'database:'+db,'population':'fixed_output_screened',**measure([r for r in primary if r['db_id']==db])})
review_path=semantic_review_path()
if review_path.exists():
 review=json.loads(review_path.read_text());lookup={r['bundle_id']:r for r in rows}
 summary['independent_targeted_review']={'reviewed_cases':len(review),'judgments':dict(Counter(r['semantic_judgment'] for r in review)),
       'current_primary_positive_cases_in_review':sum(lookup[r['bundle_id']].get('fixed_output_screened_eligible') and lookup[r['bundle_id']].get('all_alternatives_agree') is True for r in review),'selection':'Targeted positive cohort, not a corpus validation sample; no corrected semantic-rate denominator is inferred.'}
(O/'agreement-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for name,rr in [('agreement-rates.csv',flat),('screen-exclusions.csv',exclusions)]:
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
# Preserve complete IDs for every conditional population and positive case.
(O/'primary-positive-cases.json').write_text(json.dumps([r for r in rows if r.get('fixed_output_screened_eligible') and r.get('all_alternatives_agree') is True],indent=2,ensure_ascii=False)+'\n')
print(json.dumps({ds:{p:v for p,v in summary[ds]['populations'].items() if p.startswith('fixed_output')} for ds in ['spider','bird']},indent=2))
