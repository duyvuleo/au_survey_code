"""Independent census, all-primary execution and evidence-integrity validation.

Uses direct SQLite row comparisons, not run_experiment.py's result hashing.
"""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import csv,hashlib,json,sqlite3,time

from replay_config import output_dir
from frozen_protocol import PROTOCOL_SHA256
H=Path(__file__).resolve().parent;O=output_dir()
ledger=[json.loads(s) for s in (O/'bundle-ledger.jsonl').read_text().splitlines()]
m=json.loads((O/'source-manifest.json').read_text())
assert len(ledger)==3128 and len({r['bundle_id'] for r in ledger})==len(ledger)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
 return h.hexdigest()
for src in m['inputs']:assert sha(src['path'])==src['sha256']
inputs={src['dataset']:[json.loads(s) for s in Path(src['path']).read_text().splitlines() if s.strip()] for src in m['inputs']}
coverage=defaultdict(set)
for r in ledger:
 for line in r['source_lines']:
  assert line not in coverage[r['dataset']]
  coverage[r['dataset']].add(line);src=inputs[r['dataset']][line-1]
  actual=json.dumps([src['db_id'],src['question'],src['expectedQuery'],src['usecase'].split(' - ')[0],src['ac_term'],src['selected_column'],src['similar_columns']],sort_keys=True,ensure_ascii=False)
  assert actual==r['annotation_key']
  assert hashlib.sha256(actual.encode()).hexdigest()==r['bundle_id'].split('-',1)[1]
for ds,rr in inputs.items():assert coverage[ds]=={i for i,r in enumerate(rr,1) if 'ambiguity' in r['usecase']}
assert sum(len(v) for v in coverage.values())==11827
for db in m['databases']:assert sha(db['path'])==db['sha256']
assert sha(H/'run_experiment.py')==m['script_sha256']
assert PROTOCOL_SHA256==m['protocol_sha256']

# Contract controls catch flat-cell/set/null conflations independently of data.
assert Counter([(1,2),(3,4)])!=Counter([(1,3),(2,4)])
assert Counter([(1,2)])!=Counter([(2,1)])
assert Counter([(1,),(1,)])!=Counter([(1,)])
assert Counter([(None,)])!=Counter([('NULL',)])
assert Counter([(1,)])!=Counter([('1',)])
assert Counter([(1,)])==Counter([(1.0,)])

def pred(s):return s.lower()=='true'
pairs=list(csv.DictReader((O/'pair-comparisons.csv').open()))
byid={r['bundle_id']:r for r in ledger};pp=defaultdict(list)
for p in pairs:
 r=byid[p['bundle_id']];i,j=int(p['reference_i']),int(p['reference_j'])
 assert i<j
 a,b=r['references'][i]['execution'],r['references'][j]['execution']
 assert a['ok'] and b['ok']
 assert pred(p['row_bag_equal'])==(a['bag_signature']==b['bag_signature'])
 assert pred(p['ordered_list_equal'])==(a['ordered_signature']==b['ordered_signature'])
 pp[r['bundle_id']].append(p)
for r in ledger:
 if 'references' not in r:continue
 refs=r['references'];assert len({v['sql_sha256'] for v in refs})==len(refs)
 for v in refs:assert hashlib.sha256(json.dumps(v['sql'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()==v['sql_sha256']
 complete=all(v['execution']['ok'] for v in refs) and len(refs)>1
 assert complete==r['all_alternatives_executed']
 if complete:
  signature='ordered_signature' if r['outer_order_required'] else 'bag_signature'
  unanimous=all(v['execution'][signature]==refs[0]['execution'][signature] for v in refs)
  assert unanimous==r['all_alternatives_agree']
  assert len(pp[r['bundle_id']])==len(refs)*(len(refs)-1)//2
  assert any(pred(p['declared_comparator_equal']) for p in pp[r['bundle_id']])==r['any_pair_agrees']
 else:assert r['all_alternatives_agree'] is None
 if r['fixed_output_screened_eligible']:
  assert complete and not r['fixed_output_exclusion_reasons'] and not r['category'].startswith('value')

# Independently execute every reference in the primary screened population.
dbs={(r['dataset'],r['db_id']):r for r in m['databases']};connections={}
reexec=0;cases=0;recomputed=Counter();fail=[]
for r in ledger:
 if not r['fixed_output_screened_eligible']:continue
 key=(r['dataset'],r['db_id'])
 if key not in connections:
  c=sqlite3.connect(Path(dbs[key]['path']).resolve().as_uri()+'?mode=ro',uri=True);c.execute('PRAGMA query_only=ON');connections[key]=c
 c=connections[key];outputs=[]
 for ref in r['references']:
  deadline=time.monotonic()+10;c.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
  cur=c.execute(ref['sql']);a=cur.fetchall()
  assert len(a)==ref['execution']['row_count'];assert len(cur.description)==ref['execution']['column_count']
  outputs.append(a);reexec+=1
 same=all(a==outputs[0] for a in outputs) if r['outer_order_required'] else all(Counter(a)==Counter(outputs[0]) for a in outputs)
 assert same==r['all_alternatives_agree'],r['bundle_id']
 cases+=1;recomputed[r['dataset']]+=same
for c in connections.values():c.close()
s=json.loads((O/'agreement-summary.json').read_text())
for ds in ['spider','bird']:
 assert recomputed[ds]==s[ds]['populations']['fixed_output_screened']['unanimous_agreement']
reasons=Counter(r['status'] for r in ledger)
assert not reasons['implementation_error']
v={'status':'passed','census_bundles':len(ledger),'ambiguity_conversation_rows_exactly_reconciled':11827,'all_final_records':sum(len(r) for r in inputs.values()),'database_hashes_verified':len(m['databases']),
   'pair_rows_checked':len(pairs),'primary_cases_independently_executed':cases,'primary_references_independently_executed':reexec,'primary_unanimous_counts':dict(recomputed),
   'contract_control_checks':6,'ledger_sha256':sha(O/'bundle-ledger.jsonl'),'limits':['Validates row comparisons/census/hash integrity; does not independently adjudicate all meaning, role, unit or product choices.','The source-stratified and targeted semantic reviews retain unresolved cases.']}
(O/'validation.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
