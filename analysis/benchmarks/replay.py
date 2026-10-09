#!/usr/bin/env python3
"""Optional replay of saved AmbiQT candidates and AMBROSIA gold-query checks.

Requires separately acquired, hash-matching upstream artifacts. No network,
model calls, credential handling or benchmark downloads are performed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CATEGORIES = ['col-synonyms', 'tbl-synonyms', 'tbl-split', 'tbl-agg']
WORKERS = {'ambiqt': 'replay_ambiqt.py', 'summarize': 'summarize_replay.py',
           'validate-native': 'validate_native_replay.py',
           'ambrosia': 'audit_ambrosia.py', 'oracle': 'ambrosia_oracle.py',
           'transform-identities': 'validate_transforms.py'}


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def preflight(cfg, groups):
    checked = 0
    manifest = json.loads((HERE / 'expected_sources.json').read_text())
    for item in manifest:
        group = item['group']
        if group not in groups:
            continue
        if group == 'ambiqt':
            path = Path(cfg['ambiqt_root']) / item['path']
        elif group == 'ambrosia_data_root':
            path = Path(cfg[group]) / item['path']
        else:
            path = Path(cfg[group])
        if not path.is_file() or path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
            raise SystemExit(f'Input missing or identity differs: {group}/{item["path"]}')
        checked += 1
    if not checked:
        raise SystemExit('No source groups selected.')
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=[*WORKERS, 'check-inputs', 'summarize-recorded'])
    parser.add_argument('--ambiqt-root', type=Path, help='Prepared AmbiQT layout described in README.')
    parser.add_argument('--nltk-data', type=Path, help='NLTK data directory containing tokenizers/punkt_tab.')
    parser.add_argument('--ambrosia-data-root', type=Path, help='Extracted release root containing data/ambrosia.csv.')
    parser.add_argument('--ambrosia-metrics', type=Path, help='Pinned external src/evaluation/metrics.py.')
    parser.add_argument('--ambrosia-exceptions', type=Path, help='Pinned external src/evaluation/exceptions.py.')
    parser.add_argument('--ambrosia-archive', type=Path, help='Optional original ZIP for receipt identity.')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'reproduced/benchmarks')
    parser.add_argument('--category', choices=CATEGORIES, action='append', help='AmbiQT category; repeat or omit for all.')
    parser.add_argument('--limit', type=int, help='Smoke-test prefix per model/category, or selected AMBROSIA records.')
    parser.add_argument('--record-id', action='append', default=[], help='AMBROSIA record IDs for bounded diagnostic checks.')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive.')
    if args.limit and args.command not in ('ambiqt', 'ambrosia', 'oracle'):
        parser.error('--limit only applies to SQL replay commands.')
    if args.record_id and args.command not in ('ambrosia', 'oracle'):
        parser.error('--record-id only applies to AMBROSIA.')
    out = args.output_dir.resolve()
    if out == ROOT or not out.is_relative_to(ROOT / 'reproduced'):
        parser.error('--output-dir must be a subdirectory of this package\'s reproduced/ directory.')
    cfg = {name: str(getattr(args, name).resolve()) if getattr(args, name) else None
           for name in ('ambiqt_root', 'nltk_data', 'ambrosia_data_root', 'ambrosia_metrics',
                        'ambrosia_exceptions', 'ambrosia_archive')}
    cfg.update(output_dir=str(out), categories=args.category or CATEGORIES,
               limit=args.limit, record_ids=args.record_id)
    if cfg['nltk_data'] is None and cfg['ambiqt_root']:
        cfg['nltk_data'] = str(Path(cfg['ambiqt_root']) / 'nltk_data')
    groups = set()
    if args.command in ('ambiqt', 'validate-native', 'transform-identities'):
        if not cfg['ambiqt_root']:
            parser.error('--ambiqt-root is required.')
        groups.add('ambiqt')
    if args.command in ('ambrosia', 'oracle'):
        for key in ('ambrosia_data_root', 'ambrosia_metrics', 'ambrosia_exceptions'):
            if not cfg[key]:
                parser.error('--' + key.replace('_', '-') + ' is required.')
        groups.update(('ambrosia_data_root', 'ambrosia_metrics', 'ambrosia_exceptions'))
    if args.command == 'check-inputs':
        if cfg['ambiqt_root']:
            groups.add('ambiqt')
        for key in ('ambrosia_data_root', 'ambrosia_metrics', 'ambrosia_exceptions'):
            if cfg[key]:
                groups.add(key)
    for key in ('ambiqt_root', 'ambrosia_data_root'):
        if cfg[key]:
            source = Path(cfg[key])
            if out.is_relative_to(source) or source.is_relative_to(out):
                parser.error('Output and input roots must not overlap.')
    checked = preflight(cfg, groups) if groups or args.command == 'check-inputs' else 0
    if args.command == 'check-inputs':
        print(f'Input identity passed for {checked} files. No SQL was executed.')
        return
    if cfg['ambrosia_archive'] and sha256(Path(cfg['ambrosia_archive'])) != 'a77f9cdb1f60bea69445fccc1f9f8f61146efe2ac2627f1b9e725855fac1242e':
        raise SystemExit('AMBROSIA archive identity differs.')
    out.mkdir(parents=True, exist_ok=True)
    command = args.command
    if command == 'summarize-recorded':
        for source in (HERE / 'recorded').glob('ambiqt_*'):
            shutil.copyfile(source, out / source.name)
        command = 'summarize'
    env = os.environ.copy()
    env['SURVEY_BENCHMARK_REPLAY_CONFIG'] = json.dumps(cfg)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    subprocess.run([sys.executable, '-B', str(HERE / WORKERS[command])], env=env, check=True,
                   cwd=out)
    receipt = {'command': args.command, 'passed': True, 'input_files_hash_checked': checked,
               'scope': 'bounded smoke check' if args.limit or args.record_id or args.category else
                        ('recorded-result arithmetic' if args.command in ('summarize', 'summarize-recorded') else
                         'full recorded benchmark population'),
               'record_limit': args.limit, 'record_ids': args.record_id,
               'categories': cfg['categories'], 'model_inference': False,
               'native_scorers_external': True}
    (out / f'{args.command}-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Finished. Results and receipt are under the chosen reproduced/ directory.')


if __name__ == '__main__':
    main()
