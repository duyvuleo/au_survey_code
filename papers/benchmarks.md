# Benchmarks and evaluation

These 13 settings from 11 studies are the descriptive audit population. A dash means outside the specified check, not that a benchmark lacks the capability. Interpret entries using the [audit criteria and qualifications](../analysis/data/benchmarks/benchmark-audit.json).

| Setting | Clarification | Coverage and risk | Distinct gold results | Meaning recovery |
|---|---|---|---|---|
| [AmbiQT](https://aclanthology.org/2023.emnlp-main.436/) | — | — | No check found | SQL matching |
| [AMBROSIA](https://arxiv.org/abs/2406.19073) | — | — | Required | SQL matching |
| [PRACTIQ: SQL prediction](https://aclanthology.org/2025.naacl-long.13/) | Given history | — | — | — |
| [CLARITY: multi-turn](https://aclanthology.org/2026.acl-industry.86/) | Given history | Not recoverable | — | — |
| [Sphinteract: main](https://www.vldb.org/pvldb/vol18/p1145-zhao.pdf) | System-selected | — | — | — |
| [BIRD-History](https://arxiv.org/abs/2608.29345) | — | — | — | — |
| [TrustSQL](https://arxiv.org/abs/2403.15879) | — | Derivable | — | — |
| [SCARE](https://proceedings.mlr.press/v297/lee26b.html) | — | By category | — | — |
| [ABISS: predicted category](https://arxiv.org/abs/2607.23340) | System-selected | Not recoverable | — | — |
| [TIDE-Bench: full](https://arxiv.org/abs/2608.29543) | System-selected | — | — | — |
| [TIDE-Bench: L1-primed](https://arxiv.org/abs/2608.29543) | Given + system | — | — | — |
| [BIRD-INTERACT: c-Interact](https://proceedings.iclr.cc/paper_files/paper/2026/hash/496b549556509bbb9770bf9d335c5800-Abstract-Conference.html) | System-selected | — | — | — |
| [BIRD-INTERACT: a-Interact](https://proceedings.iclr.cc/paper_files/paper/2026/hash/496b549556509bbb9770bf9d335c5800-Abstract-Conference.html) | System-selected | — | — | — |

## Numerical analyses

- **SCARE:** reconstruct response counts from rounded published scores and compare coverage, correct answers, and errors.
- **TrustSQL:** check published count/score consistency and report request coverage alongside conditional accuracy.
- **AmbiQT:** inspect reference execution and compare interpretation recovery at fixed candidate budgets.
- **AMBROSIA:** check duplicate references and how output-comparison rules affect gold-query matching.
- **CLARITY:** compare query alternatives derived from annotations, with explicit exclusions and checks of source-table contents.

See [analysis instructions](../analysis/README.md) for code, pinned inputs, and scope.
