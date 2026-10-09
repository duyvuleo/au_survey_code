# CLARITY analysis

The [frozen protocol](PROTOCOL.md) defines reference construction, output comparison, exclusions, and the interpretation of agreement rates. It is an exact Markdown copy of the protocol embedded in `frozen_protocol.py`.

Check the included counts and worked cases:

```sh
python3 analysis/clarity/verify_cases.py
```

Inputs are in `analysis/data/clarity/` and this directory. The command checks recorded outcomes, not SQL execution or the validity of interpretations.

## Optional SQL execution

Provide matching annotations and databases separately. Required layouts are `ANNOTATIONS/{spider,bird}/final_data/{spider,bird}_data.jsonl` and `DATABASES/DB_ID/DB_ID.sqlite`. Hashes are in `expected_sources.py`. The public download location for the exact annotations is unverified. Database sources are the [AmbiQT snapshot](https://github.com/testzer0/AmbiQT/tree/2dd908bd4a7173f98fa6637758f4d41852722a5c) and [BIRD development archive](https://bird-bench.oss-cn-beijing.aliyuncs.com/dev.zip).

The recorded environment uses Python 3.14.7, SQLite 3.53.4, and SQLGlot 30.21.0.

```sh
python3 analysis/clarity/replay.py check-inputs \
  --annotations-root /path/to/annotations \
  --spider-databases /path/to/spider/database \
  --bird-databases /path/to/bird/dev_databases
```

With the same input arguments, run `run` and `population`, followed by `summarize` and `validate`. Outputs default to `reproduced/clarity/`. Full execution has not been repeated for this package.

For the four worked-case database checks, use `run_diagnostics.py --help`. These require the same database snapshots and use read-only connections. Generated results may contain source text, SQL, and local paths and should remain outside the submission archive.
