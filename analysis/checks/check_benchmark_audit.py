"""Check the descriptive audit population and the groups shown in Table 1."""
from pathlib import Path
from collections import Counter
import json

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ('clarification', 'coverage_risk', 'distinct_gold_results', 'meaning_recovery')


def validate_audit(audit):
    rows = audit['records']
    by_setting = {r['setting']: r for r in rows}
    assert len(by_setting) == len(rows), 'Duplicate evaluation setting'
    assert all(any(r[field] is not None for field in FIELDS) for r in rows), 'Unaudited comparison included in audit count'
    assert len(rows) == 12 and len({r['citation_key'] for r in rows}) == 10
    assert 'PersonaBIRDHistory' not in {r['citation_key'] for r in rows}
    context = audit['context_only_comparisons']
    assert len(context) == 1 and context[0]['citation_key'] == 'PersonaBIRDHistory'
    assert all(context[0][field] is None for field in FIELDS)
    clarification = Counter(r['clarification'] for r in rows if r['clarification'])
    risk = Counter(r['coverage_risk'] for r in rows if r['coverage_risk'])
    assert clarification == {'Given history': 2, 'Model-generated questions': 5, 'Given + generated': 1}
    assert risk == {'Derivable': 2, 'Insufficient aggregates': 2}
    recovery = [r for r in rows if r['meaning_recovery'] is not None]
    assert {r['citation_key'] for r in recovery} == {'M01', 'M02'}
    assert all(r['meaning_recovery'] == 'Execution match' for r in recovery)
    assert {r['distinct_gold_results'] for r in recovery} == {'Distinct, nonempty required', 'No distinctness check found'}
    ambiqt = next(r for r in rows if r['citation_key'] == 'M01')
    assert ambiqt['additional_recovery_scoring'] == ['Exact-set match']
    sphinteract = [r for r in rows if r['citation_key'] == 'PA-Sphinteract']
    assert len(sphinteract) == 1
    assert sphinteract[0]['included_variants'] == ['CQs', 'CQs & ES']
    assert sphinteract[0]['excluded_variants'] == ['Simple feedback']
    groups = audit['presentation_rows']
    assert len(groups) == 8
    assert len({(g['field'], g['finding']) for g in groups}) == len(groups)
    included = set()
    expected_cells = {(r['setting'], field) for r in rows for field in FIELDS if r[field] is not None}
    presented_cells = set()
    for group in groups:
        assert group['field'] in FIELDS
        expected = {r['setting'] for r in rows if r[group['field']] == group['finding']}
        assert expected and set(group['settings']) == expected
        assert len(group['settings']) == len(expected), 'Duplicate setting within one audit check'
        included.update(expected)
        presented_cells.update((name, group['field']) for name in expected)
    assert included == set(by_setting)
    assert presented_cells == expected_cells, 'An assessed setting/check is missing from the grouped table'
    return {
        'settings': len(rows), 'source_studies': len({r['citation_key'] for r in rows}),
        'clarification_settings': sum(clarification.values()), 'clarification_modes': dict(clarification),
        'risk_settings': sum(risk.values()), 'risk_recoverability': dict(risk),
        'interpretation_recovery_settings': len(recovery),
        'gold_distinctness': dict(Counter(r['distinct_gold_results'] for r in recovery)),
        'recovery_scoring': dict(Counter(r['meaning_recovery'] for r in recovery)),
        'presentation_rows': len(groups), 'setting_check_entries': len(presented_cells),
        'context_only_comparisons': len(context),
    }


def main():
    audit = json.loads((ROOT / 'analysis/data/benchmarks/benchmark-audit.json').read_text())
    counts = validate_audit(audit)
    scope = json.loads((ROOT / 'analysis/data/analysis-scope.json').read_text())
    assert counts['settings'] == scope['benchmark_audit_settings']
    assert counts['source_studies'] == scope['benchmark_audit_studies']
    result = {'status': 'passed', 'counts': counts,
              'scope': 'Counts and grouped findings from the included audit records. Numerical scores, SQL outcomes, and source judgments are checked separately.',
              'evidence_limits': audit['verification_boundary']}
    out = ROOT / 'reproduced/benchmark-audit.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
