# AmbiQT and AMBROSIA analysis

Saved outcomes and analysis code for the appendix checks. Run commands from the
repository root. This module performs no model training or inference.

## Recorded results

Python's standard library is sufficient:

```sh
python3 analysis/benchmarks/verify_recorded.py
python3 analysis/benchmarks/replay.py summarize-recorded
```

Outputs are written to `reproduced/benchmarks/`. These checks use saved outcomes and do not execute SQL.

## Optional execution with external inputs

Acquire upstream artifacts separately under their original terms. Input hashes
must match `expected_sources.json`; inputs are read-only and writes are confined
to a selected subdirectory of `reproduced/`. See all options with:

```sh
python3 analysis/benchmarks/replay.py --help
```

### AmbiQT

Use [revision 2dd908bd4a7173f98fa6637758f4d41852722a5c](https://github.com/testzer0/AmbiQT/tree/2dd908bd4a7173f98fa6637758f4d41852722a5c).
Prepare `AMBIQT_INPUT` outside this repository:

| Path under `AMBIQT_INPUT` | Upstream source |
|---|---|
| `{col-synonyms,tbl-synonyms,tbl-split,tbl-agg}/{evaluate.py,process_sql.py,validation.json}` | Corresponding `benchmark/<category>/` files |
| `outputs/<output-category>/{logical-beam,t5-3b-bw10}.json` | Corresponding `outputs/` files |
| `tables.json` | `spider/tables.json` |
| `README.md` | Repository `README.md` |
| `db-content/database/<db>/<db>.sqlite` | Extracted `db-content.zip` |

Output categories, in that order, are `col-synonyms`, `table-synonyms`,
`join-ambiguity`, and `precomputed-aggregates`. Expected input hashes are in `expected_sources.json`.
A checkout without this layout is not accepted directly.

The native evaluator requires NLTK, tqdm, and NLTK's `punkt_tab` resource in a
separate `NLTK_DATA` directory. Inspected versions were `nltk==3.10.3`,
`tqdm==4.70.1`, and Python 3.14.7; other runtimes may change evaluator behavior.
The wrapper does not install dependencies or download inputs.

```sh
python3 analysis/benchmarks/replay.py check-inputs --ambiqt-root /path/to/AMBIQT_INPUT
python3 analysis/benchmarks/replay.py ambiqt --ambiqt-root /path/to/AMBIQT_INPUT --nltk-data /path/to/NLTK_DATA
python3 analysis/benchmarks/replay.py summarize
python3 analysis/benchmarks/replay.py validate-native --ambiqt-root /path/to/AMBIQT_INPUT --nltk-data /path/to/NLTK_DATA
python3 analysis/benchmarks/replay.py transform-identities --ambiqt-root /path/to/AMBIQT_INPUT
```

### AMBROSIA

Obtain the dataset through the [project website](https://ambrosia-benchmark.github.io/)
and follow its access and use terms (the inspected data README specifies CC BY
4.0). Extract it outside this repository with `AMBROSIA_INPUT/data/ambrosia.csv`
and its referenced database paths. Expected input hashes are recorded in `expected_sources.json`.

Obtain `src/evaluation/metrics.py` and `src/evaluation/exceptions.py` from
[revision 7de80a41f1ad4f01aed9bb55e734654688b572a8](https://github.com/saparina/ambrosia/tree/7de80a41f1ad4f01aed9bb55e734654688b572a8).
Those unchanged modules and Python's standard library suffice.

```sh
python3 analysis/benchmarks/replay.py ambrosia \
  --ambrosia-data-root /path/to/AMBROSIA_INPUT \
  --ambrosia-metrics /path/to/ambrosia/src/evaluation/metrics.py \
  --ambrosia-exceptions /path/to/ambrosia/src/evaluation/exceptions.py

python3 analysis/benchmarks/replay.py oracle \
  --ambrosia-data-root /path/to/AMBROSIA_INPUT \
  --ambrosia-metrics /path/to/ambrosia/src/evaluation/metrics.py \
  --ambrosia-exceptions /path/to/ambrosia/src/evaluation/exceptions.py
```

`ambrosia` checks gold-query outputs. `oracle` tests the scorer using the gold queries as predictions. Use `--help` for subset checks. Full native evaluations and model inference are not rerun by the recorded-result check.
