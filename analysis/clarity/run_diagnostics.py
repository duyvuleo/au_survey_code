"""Optionally repeat four read-only explanatory checks on externally supplied DBs.

These are analysis queries, not redistributed benchmark SQL. The assertions test
recorded mechanisms and counts, not the semantic validity of all interpretations.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sqlite3

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--spider-db-root", type=Path, required=True)
ap.add_argument("--bird-db-root", type=Path, required=True)
args = ap.parse_args()
checks = [
    ("bird", "card_games", "c98bdb57fe7474da798b407785544b9af0daaad5d61fd21e2a73309493bc1227",
     "SELECT COUNT(*),COUNT(DISTINCT s.id),SUM(s.baseSetSize<>s.totalSetSize),"
     "SUM((s.baseSetSize<100)<>(s.totalSetSize<100)),SUM(s.baseSetSize IS NULL),"
     "SUM(s.totalSetSize IS NULL),SUM(s.baseSetSize<100),SUM(s.totalSetSize<100) "
     "FROM sets s JOIN set_translations t ON t.setCode=s.code "
     "WHERE t.translation IS NOT NULL AND t.language='Italian'",
     [95,95,16,0,0,0,30,30]),
    ("spider", "hr_1", "5e3358561f210b2f75d9ced5eafc13744c773f3f27eb8e0967afddd21fb25350",
     "SELECT COUNT(*),SUM(min_salary IS NULL),SUM(max_salary IS NULL),SUM(min_salary>max_salary),"
     "SUM(min_salary>9000),SUM(max_salary>9000) FROM jobs", [19,0,0,0,3,10]),
    ("spider", "music_2", "1d2ab9310c84c5acb0c2b30f0ba52898d73a86a89c721131032260c827bdf8b9",
     "SELECT (SELECT COUNT(*) FROM Band),(SELECT COUNT(*) FROM Instruments)", [0,0]),
    ("spider", "store_product", "f36004a47e0a221b56b5eab99198f0f234161399f745545b9a39338ca77a64ba",
     "SELECT COUNT(*),SUM(max_page_size='A4'),SUM(pages_per_minute_color<5),SUM(dpi<5),"
     "SUM(pages_per_minute_color<5 AND (max_page_size IS NULL OR max_page_size<>'A4')) FROM product",
     [6,4,2,0,0]),
]
result = []
for dataset, dbid, expected_hash, sql, expected in checks:
    root = args.bird_db_root if dataset == "bird" else args.spider_db_root
    path = (root / dbid / (dbid + ".sqlite")).resolve()
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    assert before == expected_hash, (dbid, "database identity differs")
    con = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    rows = con.execute(sql).fetchall()
    con.close()
    assert rows == [tuple(expected)], (dbid, rows)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    result.append({"dataset": dataset, "database": dbid, "sha256": before,
                   "observed": list(rows[0]), "read_only": True, "bytes_unchanged": True})
report = {"status": "pass", "checks": result,
          "scope": "Four targeted diagnostic queries on pinned instances. No model inference, broad SQL replay, new semantic labels, or membership changes."}
(HERE / "reproduced").mkdir(exist_ok=True)
(HERE / "reproduced/diagnostic-validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
