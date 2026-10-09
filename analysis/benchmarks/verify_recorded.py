#!/usr/bin/env python3
"""Recompute appendix AmbiQT and AMBROSIA claims from saved records.

Uses only the standard library. No SQL, native evaluator, network or model calls.
This validates recorded-score arithmetic, not upstream execution or semantics.
"""
from collections import Counter
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / 'recorded'
OUT = HERE.parents[1] / 'reproduced/benchmarks'


def jsonl(name):
    return [json.loads(line) for line in (DATA / name).read_text().splitlines() if line.strip()]


def equal(x, y):
    assert math.isclose(x, y, abs_tol=1e-12, rel_tol=1e-12), (x, y)


def main():
    categories = ['col-synonyms', 'tbl-synonyms', 'tbl-split', 'tbl-agg']
    models = ['logical-beam', 't5-3b-bw10']
    expected_n = [1129, 1312, 251, 96]
    expected_pct = {'logical-beam': [40.48, 54.65, 76.89, 26.04],
                    't5-3b-bw10': [16.12, 29.88, 34.66, 17.71]}
    fixed = list(csv.DictReader((DATA / 'ambiqt_fixed_common_population.csv').open()))
    actual = []
    failed_gold = set()
    source_n = 0
    for cat, expected in zip(categories, expected_n):
        records = {model: jsonl(f'ambiqt_{cat}_{model}_records.jsonl') for model in models}
        n = len(records[models[0]])
        source_n += n
        assert n == len(records[models[1]])
        for model in models:
            assert [r['index'] for r in records[model]] == list(range(n))
            for r in records[model]:
                assert r['gold_status']['parse_ok']
                if not r['gold_status']['execute_ok']:
                    failed_gold.add((cat, r['index']))
        for i in range(n):
            assert records[models[0]][i]['question_sha256'] == records[models[1]][i]['question_sha256']
        ids = [i for i in range(n) if all(records[m][i]['pool_count'] >= 10 and
               records[m][i]['gold_status']['parse_ok'] and
               records[m][i]['gold_status']['execute_ok'] for m in models)]
        assert len(ids) == expected
        for model in models:
            for budget in [1, 2, 3, 5, 10]:
                for comparator in ['exact', 'native_exec', 'direct_exec']:
                    either = both = 0
                    for i in ids:
                        candidates = records[model][i]['candidate_scores'][:budget]
                        flags = [any(c['alternatives'][j][comparator] == 1 for c in candidates) for j in [0, 1]]
                        either += any(flags)
                        both += all(flags)
                    saved = [r for r in fixed if r['category'] == cat and r['model'] == model and
                             int(r['budget']) == budget and r['comparator'] == comparator]
                    assert len(saved) == 1
                    saved = saved[0]
                    assert int(saved['N']) == expected
                    assert int(saved['either_count']) == either and int(saved['both_count']) == both
                    equal(float(saved['either_rate']), either / expected)
                    equal(float(saved['both_rate']), both / expected)
                    if budget == 10 and comparator == 'native_exec':
                        assert round(100 * both / expected, 2) == expected_pct[model][categories.index(cat)]
                        actual.append({'category': cat, 'model': model, 'N': expected,
                                       'both_at_10': both, 'percentage': 100 * both / expected})
    assert source_n == 3046 and len(failed_gold) == 10
    records = jsonl('ambrosia_records.jsonl')
    pairs = list(csv.DictReader((DATA / 'ambrosia_pair_comparisons.csv').open()))
    oracle = json.loads((DATA / 'ambrosia_gold_oracle.json').read_text())
    assert len(records) == 1277 and len({r['record_id'] for r in records}) == 1277
    assert sum(r['gold_count'] for r in records) == 2965
    assert all(r['all_gold_executed'] and r['all_gold_nonempty'] for r in records)
    assert len(pairs) == 2099
    pair_counts = {key: sum(r[key] == 'True' for r in pairs) for key in
                   ['exact_list_match', 'row_bag_match', 'row_set_match']}
    assert pair_counts == {'exact_list_match': 2, 'row_bag_match': 9, 'row_set_match': 16}
    native = [r for r in pairs if r['native_i_to_j'] == 'True' or r['native_j_to_i'] == 'True']
    assert len(native) == 3
    assert {r['record_id'] for r in native} == {'613', '3600', '3677'}
    assert all(r['row_bag_match'] == 'True' for r in native)
    test = [r for r in oracle if r['split'] == 'test']
    assert len(test) == 1149 and sum(r['all_found'] for r in test) == 1147
    nonperfect = [r for r in test if not r['all_found']]
    assert {r['record_id'] for r in nonperfect} == {'3600', '3677'}
    for r in nonperfect:
        assert r['gold_list_count'] == 3 and r['gold_unique_sql_count'] == 2
        equal(r['recall'], 2 / 3)
    recall = sum(r['recall'] for r in test) / len(test)
    equal(recall, 1 - 2 / (3 * 1149))
    receipt = {'passed': True, 'scope': 'Saved outcome arithmetic only; no SQL or semantic validation.',
               'ambiqt_source_requests': source_n, 'ambiqt_failed_gold_requests': len(failed_gold),
               'ambiqt_fixed_population_results': actual, 'ambrosia_requests': len(records),
               'ambrosia_gold_entries': 2965, 'ambrosia_pairs': len(pairs),
               'ambrosia_pair_matches': pair_counts, 'ambrosia_native_matching_pairs': len(native),
               'ambrosia_test_recall_pct': 100 * recall,
               'ambrosia_test_all_found': 1147, 'ambrosia_duplicate_gold_ids': ['3600', '3677']}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'recorded-validation.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('AmbiQT fixed-population rates and AMBROSIA comparator/oracle counts passed.')


if __name__ == '__main__':
    main()
