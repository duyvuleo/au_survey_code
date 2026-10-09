"""Check anonymous relationship evidence against the reported analysis."""
from collections import Counter
from pathlib import Path
import csv
import hashlib
import json
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
REL = ROOT / "analysis/data/overlap/relationships"
REV = REL / "reviews"
inputs = {}


def read(path, as_csv=False):
    raw = path.read_bytes()
    inputs[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
    return list(csv.DictReader(raw.decode("utf-8-sig").splitlines())) if as_csv else json.loads(raw)


def keyed(rows, field):
    result = {r[field]: r for r in rows}
    assert len(result) == len(rows), (field, "duplicate IDs")
    return result


forms = {name: keyed(read(REV / f"{name}.csv", True), "case_id") for name in ["reviewer-a", "reviewer-b"]}
decisions = keyed(read(REV / "resolutions.json"), "case_id")
verification = read(REV / "verification.json")
records = keyed(read(REL / "outputs/strict-analysis-records.json"), "setting_id")
sources = read(REL / "source-records.json")
descriptions = keyed(sources["settings"], "setting_id")
assert len(records) == 89 and set(records) == set(descriptions)
assert len(decisions) == 36 and all(set(f) == set(decisions) for f in forms.values())
fields = {"information_flow_PNU": "integration", "empirical_evaluation_PNU": "relationship_evaluation"}
disagreements = []
agreement = Counter()
for case, final in decisions.items():
    submitted = {name: form[case] for name, form in forms.items()}
    for name, row in submitted.items():
        assert (row["setting_id"], row["pair"]) == (final["setting_id"], final["pair"])
        for field in fields:
            assert row[field] == final["submitted_core_judgments"][name][field]
        for field, value in final["submitted_ib_subtypes"][name].items():
            assert (row[field] or None) == value, "Blank subtype entries must remain missing"
    for field, prop in fields.items():
        values = [r[field] for r in submitted.values()]
        if values[0] == values[1]:
            agreement[field] += 1
            assert final[prop] == values[0]
        else:
            rule = final["resolution"]
            assert rule["field"] == field and rule["status"] == final[prop]
            assert rule["rationale"] and rule["source_url"]
            disagreements.append({"case_id": case, "field": field, "decision": final[prop]})
    if final["pair"] != "BV":
        assert records[final["setting_id"]]["connections"][final["pair"]] == {prop: final[prop] for prop in fields.values()}
    if final["empirical_evidence_types"]:
        assert final["pair"] == "IB" and final["relationship_evaluation"] == "P"
for field in fields:
    saved = verification["submitted_form_agreement"][field]
    assert saved["matching"] == agreement[field] and saved["paired"] == len(decisions)
    assert abs(saved["percent"] - 100 * agreement[field] / len(decisions)) < 1e-10
assert len(disagreements) == 3
for sid, record in records.items():
    description = descriptions[sid]
    assert description["paper_id"] == record["paper_id"]
    assert description["setting"] and description["source_url"]
    for endpoint, node in description["perspectives"].items():
        assert node["status"] == record["states"][endpoint]
        assert node["rationale"] and node["source_locators"]
        assert all(key in sources["source_locators"] for key in node["source_locators"])
    for pair, node in description["relationships"].items():
        if "review_case_id" in node:
            case = decisions[node["review_case_id"]]
            assert (case["setting_id"], case["pair"]) == (sid, pair)
            assert node["judgments"] == record["connections"][pair]
        else:
            for prop, evidence in node.items():
                assert evidence["status"] == record["connections"][pair][prop]
                assert evidence["rationale"] and evidence["source_locators"]
                assert all(key in sources["source_locators"] for key in evidence["source_locators"])
for source in sources["source_locators"].values():
    parsed = urlparse(source["source_url"])
    assert parsed.scheme in ["http", "https"] and parsed.netloc
result = {
    "status": "pass", "revision": verification["revision"],
    "setting_descriptions": len(descriptions), "review_cases": len(decisions),
    "submitted_form_agreement": dict(agreement), "disagreement_resolutions": disagreements,
    "source_locators": len(sources["source_locators"]), "input_sha256": inputs,
    "scope": "Checks preserved forms, source metadata, resolved labels, and numerical linkage. Does not repeat source inspection or human review.",
}
for path, expected in inputs.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
output = ROOT / "reproduced/relationship-review-validation.json"
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ["status", "revision", "setting_descriptions", "review_cases", "source_locators"]}))
