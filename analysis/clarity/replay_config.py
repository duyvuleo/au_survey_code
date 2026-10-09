"""Path configuration only; scientific transformations live in copied modules."""
import os
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]


def configured(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Set {name} through replay.py's explicit path arguments.")
    return Path(value).expanduser().resolve()


def annotations_root():
    return configured("CLARITY_ANNOTATIONS_ROOT")


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
