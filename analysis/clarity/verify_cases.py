"""Check CLARITY case identity and population accounting from saved evidence."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--repo-root", type=Path, default=HERE.parents[1],
                help="Repository root (defaults to the root containing this script).")
args = ap.parse_args()
ledger_path = args.repo_root.resolve() / "analysis/data/clarity/outputs/bundle-ledger.jsonl"
content = ledger_path.read_bytes()
assert hashlib.sha256(content).hexdigest() == "f422c687e1776948a8e5583cdf6a3b119bfa94669e8237bf282955e41712e0ab", "CLARITY ledger identity differs"
rows = [json.loads(line) for line in content.splitlines()]
by_id = {r["bundle_id"]: r for r in rows}
assert len(by_id) == len(rows) == 3128
column_categories = {"lexical column ambiguity single", "lexical column ambiguity multiple",
                     "semantic column ambiguity single", "semantic column ambiguity multiple"}
col = [r for r in rows if r["category"] in column_categories]
primary = [r for r in rows if r["fixed_output_screened_eligible"]]
expected = json.loads((HERE / "population.json").read_text())
for name, population in [("all_cases", rows), ("column_cases", col), ("primary_cases", primary)]:
    counts = Counter(r["dataset"] for r in population)
    counts["combined"] = len(population)
    assert dict(counts) == expected[name], (name, counts)
partition = Counter()
for r in col:
    if r["status"] in {"parent_execution_failed", "construction_unresolved", "alternative_execution_incomplete"}:
        partition[r["status"]] += 1
    else:
        assert r["status"] == "complete_execution"
        partition["retained_primary" if r["fixed_output_screened_eligible"] else "complete_screen_excluded"] += 1
assert dict(partition) == expected["column_partition"]
assert all(r.get("outer_order_required") is False for r in primary)
flag = "outer_order_requires_tie_validation"
complete = [r for r in col if r["status"] == "complete_execution"]
assert sum(flag in r["fixed_output_exclusion_reasons"] for r in complete) == 415
assert sum(set(r["fixed_output_exclusion_reasons"]) == {flag} for r in complete) == 40
cases = json.loads((HERE / "worked-cases.json").read_text())["cases"]
assert len(cases) == 4
for c in cases:
    r = by_id[c["bundle_id"]]
    assert r["fixed_output_screened_eligible"] and len(r["references"]) == 2
    assert r["first_source_line"] == c["source"]["line_1based"]
    assert r["dataset"] == c["dataset"] and r["db_id"] == c["db_id"]
    for source, supplied in zip(r["references"], c["reference_records"]):
        assert source["sql_sha256"] == supplied["sql_sha256"]
        for k in ["row_count", "column_count", "bag_signature", "ordered_signature", "empty", "scalar_zero"]:
            assert source["execution"][k] == supplied[k], (c["case_id"], k)
    for k, v in c["outcome"].items():
        assert r[k] == v, (c["case_id"], k)
report = {"status": "pass", "all_cases": 3128, "column_cases": 1640, "primary_cases": 319,
          "worked_cases": 4, "represented_queries": 8,
          "retention_percent": {"all_cases": 100*319/3128, "column_cases": 100*319/1640},
          "scope": "Saved counts, signatures and identities only. No SQL execution or semantic review is repeated. Independent human validation is not included."}
(HERE / "reproduced").mkdir(exist_ok=True)
(HERE / "reproduced/validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
