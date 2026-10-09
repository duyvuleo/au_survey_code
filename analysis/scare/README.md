# SCARE analysis

```sh
python3 analysis/scare/check_tradeoff.py
```

The script reconstructs counts compatible with the rounded SCARE scores and checks response tradeoffs using exact arithmetic. Inputs are in `analysis/data/benchmarks/`. Results are written to `analysis/scare/reproduced/`.

Source: [SCARE, Tables 2–3](https://proceedings.mlr.press/v297/lee26b.html). The analysis assumes pooled counts and keeps the observed responses and class proportions fixed. Utility crossings are comparisons of those responses, not deployment thresholds. The exact evaluator and predictions used for the published results remain unverified.
