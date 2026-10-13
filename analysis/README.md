# Analysis code

The default workflow checks the recorded calculations supporting the paper's Analysis and Evaluation section and Analysis Details appendix. From the repository root, run:

```sh
python3 analysis/run.py
```

Use Python 3.10 or later; no dependency installation is needed. The command makes no network requests or model calls and does not execute SQL against external databases. It exits with code `0` when every check passes and with code `1` when a check fails.

The literature discussion includes work published through 05 October 2026. These analyses use a fixed corpus with a publication cutoff of 01 October 2026. PlanPool and FALCON are excluded by the analysis cutoff. After excluding C12, the analysis contains 108 settings from 62 papers. The overlap map uses 88 direct NL2SQL settings from 49 papers. The 36 human-review cases are unchanged. The descriptive audit contains 12 settings from 10 studies. BIRD-History remains a retrieval-only comparison outside that audit.

## Paper results and code

| Paper result | Code used by the default run | Inputs | Generated result |
|---|---|---|---|
| Perspective connections, Jaccard overlap, and Consequence sensitivity | `run.py` | [Fixed setting assignments and counts](data/overlap/) | `reproduced/perspective-calculations.json` |
| Descriptive audit of 12 evaluation settings | [Benchmark audit check](checks/check_benchmark_audit.py) | [Audit records and qualifications](data/benchmarks/benchmark-audit.json) | `reproduced/benchmark-audit.json` |
| SCARE response counts and coverage/error ranges | `run.py` | [Published-score inputs](data/benchmarks/inputs/scare_table3.csv) | `reproduced/scare-reconstruction.json` |
| SCARE response tradeoffs | [Tradeoff calculation](scare/check_tradeoff.py) | [Recorded tradeoff receipt](scare/scare-tradeoff-receipt.json) and the score inputs above | `analysis/scare/reproduced/scare-tradeoff-receipt.json` |
| TrustSQL count/score consistency, coverage, and excluded cells | `run.py` | [Transcribed counts](data/benchmarks/inputs/trustsql_count_records.csv) and [stored comparisons](data/benchmarks/outputs/) | `reproduced/trustsql-reconstruction.json` |
| AmbiQT fixed-budget recovery and AMBROSIA query/scorer checks | [Recorded benchmark check](benchmarks/verify_recorded.py) | [Recorded benchmark outcomes](benchmarks/recorded/) | `reproduced/benchmarks/recorded-validation.json` |
| CLARITY conditional agreement and sensitivity populations | `run.py` | [Bundle and pair ledgers](data/clarity/outputs/) | `reproduced/clarity-calculations.json` |
| CLARITY population accounting and four worked cases | [Case check](clarity/verify_cases.py) | [Population](clarity/population.json), [worked cases](clarity/worked-cases.json), and the bundle ledger | `analysis/clarity/reproduced/validation.json` |
| Relationship source records, submitted forms, and final decisions | [Relationship review check](checks/check_relationship_reviews.py) | [88 setting descriptions and 36 review cases](data/overlap/relationships/) | `reproduced/relationship-review-validation.json` |
| Consistency of recorded CLARITY review summaries | [Recorded-review check](checks/check_recorded_reviews.py) | [Recorded reviews](data/clarity/independent-review/) | `reproduced/recorded-review-validation.json` |

The overall receipt is `reproduced/numeric-validation.json`. It records check status, input hashes, and the verification boundary. The [input guide](data/README.md) explains the fixed records and their fields. Directory names such as `data/*/outputs/` refer to outputs of the original analyses retained as inputs here; rerunning writes new results only to `reproduced/` directories.

To inspect AmbiQT results at each candidate budget and AMBROSIA comparison summaries, also run:

```sh
python3 analysis/benchmarks/replay.py summarize-recorded
```

This reads the same saved outcomes and writes CSV/JSON summaries under `reproduced/benchmarks/`.

## What the checks establish

The default run recomputes the reported counts, rates, score reconstructions, and consistency checks from fixed records. It verifies that tracked inputs remain unchanged during the run. The SCARE ranges reflect score rounding, and the overlap ranges reflect unresolved assignments; neither is a confidence interval.

Source-table transcription, interpretation validity, scientific coding judgments, and database outcomes are not independently reassessed by this command. The recorded-review check checks stored review summaries; it does not repeat the review. CLARITY agreement is conditional on the annotations, derived SQL, database instances, and declared screening criteria. It is not reproduction of CLARITY's published model scores.

## Optional execution with external data

- [AmbiQT and AMBROSIA](benchmarks/README.md): replay the benchmark evaluations with pinned upstream code, predictions, and databases.
- [CLARITY](clarity/README.md): construct and execute query alternatives, or rerun the four worked-case diagnostics.
- [SCARE](scare/README.md): inspect the fixed-response tradeoff calculation; this is already included in the default run and needs no external data.

Obtain external data through the upstream access procedures and follow their licenses. We obtained CLARITY's code and dataset from its authors. They were later made available in the [public repository](https://github.com/duyvuleo/clarity). The [replay guide](clarity/README.md) records the separate check of the public revision and annotation hashes. Optional replay outputs may contain source text, SQL, and local paths and should be kept out of the submission archive.
