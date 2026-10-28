"""Verify the explorer preserves corpus boundaries and source provenance."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_explorer import SOURCES, build, serialized


class ExplorerDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build()
        cls.papers = {p["id"]: p for p in cls.data["papers"]}

    def test_population_boundaries(self):
        papers = self.data["papers"]
        self.assertEqual(len(papers), 69)
        self.assertEqual(sum(p["scope"] == "analysis" for p in papers), 62)
        self.assertEqual(sum(p["scope"] == "survey" for p in papers), 5)
        self.assertEqual(sum(len(p["settings"]) for p in papers), 88)
        self.assertEqual(sum(bool(p["settings"]) for p in papers), 49)
        self.assertEqual(sum(len(p["audits"]) for p in papers), 12)
        self.assertEqual(sum(bool(p["audits"]) for p in papers), 10)

    def test_literature_additions_do_not_enter_quantitative_counts(self):
        for paper_id in ["FALCON2026", "PlanPool2026"]:
            paper = self.papers[paper_id]
            self.assertEqual(paper["scope"], "literature")
            self.assertEqual(paper["settings"], [])
            self.assertEqual(paper["audits"], [])
            self.assertIn("cutoff", paper["exclusion"]["reason"])
        self.assertNotIn("C12", self.papers)

    def test_reading_groups_are_not_setting_assignments(self):
        clarity = self.papers["M05"]
        self.assertEqual(clarity["group"], "Interpretation")
        self.assertTrue(all(s["states"]["A"] == "N" for s in clarity["settings"]))
        self.assertTrue(any(s["states"]["B"] == "P" for s in clarity["settings"]))
        self.assertTrue(any(s["states"]["C"] == "U" for s in self.papers["M07"]["settings"]))

    def test_friendly_names_and_source_ids(self):
        self.assertEqual(self.papers["S14"]["name"], "SCARE")
        self.assertEqual(self.papers["M05"]["name"], "CLARITY")
        self.assertEqual(self.papers["A01"]["name"], "NaLIR")
        self.assertTrue(all(p["name"] != p["id"] for p in self.data["papers"]))
        for paper in self.data["papers"]:
            self.assertTrue(paper["title"])
            self.assertTrue(paper["url"].startswith("https://"))
            self.assertTrue(all(s["paper_id"] == paper["id"] for s in paper["settings"]))

    def test_audit_nulls_and_qualifications_remain_explicit(self):
        audit = self.papers["M05"]["audits"][0]
        self.assertIsNone(audit["distinct_gold_results"])
        self.assertEqual(audit["coverage_risk"], "Insufficient aggregates")
        self.assertIn("reporting limit", self.data["auditQualifications"][audit["coverage_risk"]])
        self.assertFalse(self.papers["PersonaBIRDHistory"]["audits"])

    def test_reproducible_build_and_provenance(self):
        self.assertEqual((ROOT / "site/data.js").read_text(), serialized(self.data))
        for source in self.data["provenance"]:
            self.assertEqual(hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest(), source["sha256"])

    def test_conflicting_assignments_fail_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for source in SOURCES.values():
                target = root / source
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / source, target)
            target = root / SOURCES["strict"]
            strict = json.loads(target.read_text())
            strict[0]["states"]["I"] = "N"
            target.write_text(json.dumps(strict))
            with self.assertRaisesRegex(ValueError, "Endpoint records disagree"):
                build(root)


if __name__ == "__main__":
    unittest.main()
