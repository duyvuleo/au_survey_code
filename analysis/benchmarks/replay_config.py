"""Configuration supplied by the public command-line entry point."""
import json
import os


def config():
    value = os.environ.get('SURVEY_BENCHMARK_REPLAY_CONFIG')
    if not value:
        raise SystemExit('Use analysis/benchmarks/replay.py; do not invoke worker scripts directly.')
    return json.loads(value)
