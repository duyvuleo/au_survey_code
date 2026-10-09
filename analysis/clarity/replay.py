#!/usr/bin/env python3
"""Optional external-data replay. Summary reproduction does not require this run."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
from expected_sources import ANNOTATIONS, DATABASES, METADATA
from replay_config import output_dir


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_sources(args, parser):
    for field in ("annotations_root", "spider_databases", "bird_databases"):
        value = getattr(args, field)
        if value is None or not value.is_dir():
            parser.error(f"--{field.replace('_', '-')} must name an existing external directory")
    for dataset, record in ANNOTATIONS.items():
        path = args.annotations_root / record["relative_path"]
        if not path.is_file() or sha(path) != record["sha256"]:
            parser.error(f"Annotation input does not match the frozen SHA-256: {dataset}")
    for identity, record in DATABASES.items():
        dataset = identity.split("/", 1)[0]
        root = args.spider_databases if dataset == "spider" else args.bird_databases
        path = root / record["relative_path"]
        if not path.is_file() or path.stat().st_size != record["bytes"] or sha(path) != record["sha256"]:
            parser.error(f"Database does not match the frozen byte count/SHA-256: {identity}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check-inputs", "run", "population", "summarize", "validate"))
    parser.add_argument("--annotations-root", type=Path)
    parser.add_argument("--spider-databases", type=Path)
    parser.add_argument("--bird-databases", type=Path)
    parser.add_argument("--output-dir", type=Path, help="Default: package/reproduced/clarity")
    parser.add_argument("--semantic-review", type=Path, help="Optional saved targeted-positive judgments for summarization")
    args = parser.parse_args()
    if args.action in ("check-inputs", "run", "population"):
        check_sources(args, parser)
    for attribute, environment in (
        ("annotations_root", "CLARITY_ANNOTATIONS_ROOT"),
        ("spider_databases", "CLARITY_SPIDER_DATABASES"),
        ("bird_databases", "CLARITY_BIRD_DATABASES"),
        ("output_dir", "CLARITY_OUTPUT_DIR"),
        ("semantic_review", "CLARITY_SEMANTIC_REVIEW"),
    ):
        value = getattr(args, attribute)
        if value is not None:
            os.environ[environment] = str(value.expanduser().resolve())
    if args.action == "check-inputs":
        print("External annotation and used-database hashes match the frozen run; no SQL executed.")
        return
    if args.action in ("run", "population"):
        import sqlglot
        if sqlglot.__version__ != METADATA["sqlglot"]:
            parser.error(f"This replay requires sqlglot=={METADATA['sqlglot']}")
    destination = output_dir()
    destination.mkdir(parents=True, exist_ok=True)
    scripts = {"run": "run_experiment.py", "population": "audit_population.py", "summarize": "summarize.py", "validate": "validate.py"}
    script = HERE / scripts[args.action]
    previous = sys.argv
    sys.argv = [str(script)] + (["--dataset", "both"] if args.action == "run" else [])
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = previous
    # Additional provenance only; canonical result calculations are unchanged.
    receipt = {
        "action": args.action,
        "run_time_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_date": METADATA["source_run_date"],
        "canonical_script_sha256": METADATA["canonical_script_sha256"],
        "configured_script_sha256": {name: sha(HERE / name) for name in METADATA["canonical_script_sha256"]},
        "adaptation": "Explicit path configuration, embedded frozen protocol identity, and optional semantic-review path only.",
        "scope": "No original model inference or author-snapshot equivalence claim.",
    }
    (destination / f"portable-{args.action}-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
