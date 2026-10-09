"""Check descriptive benchmark-audit counts."""
from pathlib import Path
from collections import Counter
import json

ROOT = Path(__file__).resolve().parents[2]
(ROOT / "reproduced").mkdir(exist_ok=True)
audit = json.loads((ROOT / 'analysis/data/benchmarks/benchmark-audit.json').read_text())
rows = audit['records']
assert len({r['setting'] for r in rows}) == len(rows), 'Duplicate evaluation setting'
clarification = Counter(r['clarification'] for r in rows if r['clarification'])
risk = Counter(r['coverage_risk'] for r in rows if r['coverage_risk'])
recovery = [r for r in rows if r['meaning_recovery'] is not None]
counts = {
    'settings': len(rows),
    'source_studies': len({r['citation_key'] for r in rows}),
    'clarification_settings': sum(clarification.values()),
    'clarification_modes': dict(clarification),
    'risk_settings': sum(risk.values()),
    'risk_recoverability': dict(risk),
    'interpretation_recovery_settings': len(recovery),
    'gold_distinctness': dict(Counter(r['distinct_gold_results'] for r in recovery)),
    'recovery_scoring': dict(Counter(r['meaning_recovery'] for r in recovery)),
}
assert counts['settings'] == 13 and counts['source_studies'] == 11
assert clarification == {'Supplied history': 2, 'System-selected': 5, 'Supplied + system': 1}
assert risk == {'Not recoverable': 2, 'Derivable': 1, 'By category': 1}
assert len(recovery) == 2 and all(r['meaning_recovery'] == 'SQL matching' for r in recovery)
assert {r['distinct_gold_results'] for r in recovery} == {'Required', 'No check found'}
result = {
    'status': 'passed',
    'counts': counts,
    'scope': 'Counts from the included benchmark-audit records. Numerical scores and SQL outcomes are checked separately.',
    'evidence_limits': audit['verification_boundary'],
}
out = ROOT / 'reproduced/benchmark-audit.json'
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
