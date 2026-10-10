"""Path configuration only; scientific transformations live in copied modules."""
import os
import hashlib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]


def configured(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Set {name} through replay.py's explicit path arguments.")
    return Path(value).expanduser().resolve()


def annotations_root():
    return configured("CLARITY_ANNOTATIONS_ROOT")


def annotation_path(dataset, root=None):
    """Accept public and original layouts without choosing conflicting files."""
    if dataset not in ("spider", "bird"):
        raise ValueError(f"Unknown annotation dataset: {dataset}")
    root = Path(root).expanduser().resolve() if root is not None else annotations_root()
    candidates = [root / dataset / "annotations.jsonl",
                  root / dataset / "final_data" / f"{dataset}_data.jsonl"]
    present = [p for p in candidates if p.is_file()]
    if not present:
        raise FileNotFoundError(f"No public or original annotation file found for {dataset}")
    if len(present) == 2 and file_sha256(present[0]) != file_sha256(present[1]):
        raise ValueError(f"Conflicting public and original annotation files: {dataset}")
    return present[0]


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def spider_databases():
    return configured("CLARITY_SPIDER_DATABASES")


def bird_databases():
    return configured("CLARITY_BIRD_DATABASES")


def output_dir():
    value = os.environ.get("CLARITY_OUTPUT_DIR")
    return Path(value).expanduser().resolve() if value else PACKAGE / "reproduced/clarity"


def semantic_review_path():
    value = os.environ.get("CLARITY_SEMANTIC_REVIEW")
    return Path(value).expanduser().resolve() if value else output_dir() / "targeted-positive-review.json"
