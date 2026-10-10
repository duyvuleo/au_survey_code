# CLARITY analysis

The [frozen protocol](PROTOCOL.md) defines reference construction, output comparison, exclusions, and the interpretation of agreement rates. It is an exact Markdown copy of the protocol embedded in `frozen_protocol.py`.

Check the included counts and worked cases:

```sh
python3 analysis/clarity/verify_cases.py
```

Inputs are in `analysis/data/clarity/` and this directory. The command checks recorded outcomes, not SQL execution or the validity of interpretations.

## Optional SQL execution

CLARITY code and annotations are available at [https://github.com/duyvuleo/clarity](https://github.com/duyvuleo/clarity). We checked [revision `ce38e0b`](https://github.com/duyvuleo/clarity/tree/ce38e0bff6e97c977d66b6abb44e0c28644aa9f1) on 10 October 2026. The public `data/spider/annotations.jsonl` and `data/bird/annotations.jsonl` files match the frozen SHA-256 hashes in `expected_sources.py`: 12,098 Spider records and 7,170 BIRD records. The [verification record](public-source.json) gives the full revision and hashes.

To use those files, clone the repository and select the checked revision:

```sh
git clone https://github.com/duyvuleo/clarity.git
git -C clarity checkout ce38e0bff6e97c977d66b6abb44e0c28644aa9f1
```

Pass the checkout's `data` directory as `--annotations-root`. The earlier `ANNOTATIONS/{spider,bird}/final_data/{spider,bird}_data.jsonl` layout is also accepted. Both layouts must match the same frozen hashes. If both layouts exist with different contents, the replay stops.

SQLite databases are separate. Required database paths are `DATABASES/DB_ID/DB_ID.sqlite`. Use the [AmbiQT snapshot](https://github.com/testzer0/AmbiQT/tree/2dd908bd4a7173f98fa6637758f4d41852722a5c) for the Spider files used here and the [BIRD development archive](https://bird-bench.oss-cn-beijing.aliyuncs.com/dev.zip). The source checks enforce the database hashes in `expected_sources.py`. Matching the annotations does not verify CLARITY's original database snapshots or reproduce its published model scores.

The recorded environment uses Python 3.14.7, SQLite 3.53.4, and SQLGlot 30.21.0.

```sh
python3 analysis/clarity/replay.py check-inputs \
  --annotations-root /path/to/clarity/data \
  --spider-databases /path/to/spider/database \
  --bird-databases /path/to/bird/dev_databases
```

With the same input arguments, run `run` and `population`, followed by `summarize` and `validate`. Outputs default to `reproduced/clarity/`. Full execution has not been repeated for this package.

For the four worked-case database checks, use `run_diagnostics.py --help`. These require the same database snapshots and use read-only connections. Generated results may contain source text, SQL, and local paths and should remain outside the submission archive.
