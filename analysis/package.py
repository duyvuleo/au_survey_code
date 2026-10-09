#!/usr/bin/env python3
"""Check the recorded analyses and build a clean, reproducible submission ZIP."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = "submitted_survey_repo"
SKIP_DIRS = {"reproduced", "__pycache__", ".git", ".pytest_cache"}
SOURCE_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".csv"}


def source_files():
    files = [Path("README.md"), Path(".gitignore")]
    for directory in ("papers", "analysis", "assets"):
        suffixes = {".svg", ".png"} if directory == "assets" else SOURCE_SUFFIXES
        for path in sorted((ROOT / directory).rglob("*")):
            relative = path.relative_to(ROOT)
            if any(part in SKIP_DIRS or part.startswith(".venv")
                   for part in relative.parts):
                continue
            if path.name == ".DS_Store" or path.name.startswith("._"):
                continue
            if path.is_symlink():
                raise ValueError(f"Submission inputs must not be symlinks: {relative}")
            if path.is_file():
                if path.suffix not in suffixes:
                    raise ValueError(f"Unexpected submission file: {relative}")
                files.append(relative)
    for relative in files:
        if not (ROOT / relative).is_file() or (ROOT / relative).is_symlink():
            raise ValueError(f"Required source file missing or symlinked: {relative}")
    return sorted(files)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT.parent / f"{ARCHIVE_ROOT}.zip",
                        help="ZIP location outside the repository; default: beside it.")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.suffix != ".zip" or output.is_relative_to(ROOT):
        parser.error("--output must be a .zip path outside the repository")

    try:
        files = source_files()
        with tempfile.TemporaryDirectory(prefix="survey-submission-") as temporary:
            staging = Path(temporary) / ARCHIVE_ROOT
            hashes = {}
            for relative in files:
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                data = (ROOT / relative).read_bytes()
                target.write_bytes(data)
                hashes[relative] = sha256(data)

            print("Checking a clean temporary copy...", flush=True)
            subprocess.run([sys.executable, "analysis/run.py"], cwd=staging,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                           check=True)
            for relative, expected in hashes.items():
                if sha256((staging / relative).read_bytes()) != expected:
                    raise ValueError(f"Check changed a packaged input: {relative}")
                if sha256((ROOT / relative).read_bytes()) != expected:
                    raise ValueError(f"Source changed during packaging: {relative}")
            if source_files() != files:
                raise ValueError("Source file inventory changed during packaging")

            manifest = "".join(f"{hashes[relative]}  {relative.as_posix()}\n"
                               for relative in files)
            (staging / "SHA256SUMS").write_text(manifest, encoding="utf-8")
            staged_zip = Path(temporary) / "submission.zip"
            with zipfile.ZipFile(staged_zip, "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=9) as archive:
                for relative in sorted([*files, Path("SHA256SUMS")]):
                    info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{relative.as_posix()}",
                                           date_time=(1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, (staging / relative).read_bytes(),
                                     compresslevel=9)

            output.parent.mkdir(parents=True, exist_ok=True)
            # Write beside the destination before replacing a previous archive.
            with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".zip",
                                             delete=False) as target:
                pending = Path(target.name)
            try:
                shutil.copyfile(staged_zip, pending)
                pending.replace(output)
            finally:
                pending.unlink(missing_ok=True)
            digest = sha256(output.read_bytes())
            output.with_suffix(".zip.sha256").write_text(
                f"{digest}  {output.name}\n", encoding="utf-8")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Submission build failed: {error}", file=sys.stderr)
        return 1

    print(f"Built {output.name}: {len(files) + 1} files, {output.stat().st_size:,} bytes")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
