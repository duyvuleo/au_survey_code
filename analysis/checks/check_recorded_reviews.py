"""Check retained review counts and case IDs, not semantic validity."""
from pathlib import Path
from collections import Counter
import json

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "analysis/data/clarity"
ledger = [json.loads(line) for line in (EXP / "outputs/bundle-ledger.jsonl").open()]
known = {r["bundle_id"] for r in ledger}
positive = {r["bundle_id"] for r in ledger
            if r.get("fixed_output_screened_eligible") and r.get("all_alternatives_agree")}
targeted = json.loads((EXP / "independent-review/targeted-positive-review.json").read_text())
sample = json.loads((EXP / "independent-review/source-stratified-review.json").read_text())
assert len(targeted) == len({r["bundle_id"] for r in targeted}) == 39
assert {r["bundle_id"] for r in targeted} == positive
assert len(sample) == len({r["bundle_id"] for r in sample}) == 16
assert {r["bundle_id"] for r in sample} <= known
counts = dict(Counter(r["semantic_judgment"] for r in targeted))
saved = json.loads((EXP / "outputs/agreement-summary.json").read_text())["independent_targeted_review"]
assert saved["judgments"] == counts and saved["reviewed_cases"] == len(targeted)
report = {"status": "pass", "targeted_positive_cases": 39, "source_stratified_cases": 16,
          "recorded_judgments": counts,
          "scope": "Recorded labels and identifiers only. No new semantic or human validation."}
(ROOT / "reproduced").mkdir(exist_ok=True)
(ROOT / "reproduced/recorded-review-validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
