# Benchmarks and evaluation

Table 1 groups findings for **12 audited settings from 10 studies**. A setting can appear under more than one check. Sphinteract's clarification-question (CQs) variants, with and without early stopping (ES), count as one group. Simple feedback is excluded. The [audit records](../analysis/data/benchmarks/benchmark-audit.json) define the groups and their limits.

| Audit check | Finding | Settings audited |
|---|---|---|
| Clarification | Given history | [PRACTIQ: SQL prediction](https://aclanthology.org/2025.naacl-long.13/), [CLARITY: multi-turn](https://aclanthology.org/2026.acl-industry.86/) |
| Clarification | Model-generated questions | [Sphinteract: CQs / CQs & ES](https://www.vldb.org/pvldb/vol18/p1145-zhao.pdf), [ABISS: predicted category](https://arxiv.org/abs/2607.23340), [TIDE-Bench: full](https://arxiv.org/abs/2608.29543), [BIRD-INTERACT: c-Interact and a-Interact](https://proceedings.iclr.cc/paper_files/paper/2026/hash/496b549556509bbb9770bf9d335c5800-Abstract-Conference.html) |
| Clarification | Given + generated | [TIDE-Bench: L1-primed](https://arxiv.org/abs/2608.29543) gives first-layer resolution before the model asks about the second layer. |
| Coverage / risk | Derivable | [TrustSQL: consistent cells](https://arxiv.org/abs/2403.15879), [SCARE: two answerable categories](https://proceedings.mlr.press/v297/lee26b.html) |
| Coverage / risk | Insufficient aggregates | [CLARITY: multi-turn](https://aclanthology.org/2026.acl-industry.86/), [ABISS: predicted category](https://arxiv.org/abs/2607.23340) |
| Reference outputs | No distinctness check found | [AmbiQT: inspected generators](https://aclanthology.org/2023.emnlp-main.436/) |
| Reference outputs | Distinct, nonempty required | [AMBROSIA: construction rule](https://arxiv.org/abs/2406.19073) |
| Recovery scoring | Execution match | [AmbiQT](https://aclanthology.org/2023.emnlp-main.436/), [AMBROSIA](https://arxiv.org/abs/2406.19073) |

Coverage and risk use the same test population and each benchmark's error definition. TrustSQL excludes two inconsistent cells. SCARE calculations account for rounded published scores. “Insufficient aggregates” describes the inspected reporting, not the capability of the protocol.

Two AMBROSIA test requests contain duplicate reference SQL entries. AmbiQT also reports exact-set matching. Neither recovery score independently measures meaning coverage.

[BIRD-History](https://arxiv.org/abs/2608.29345) remains in the appendix comparison table as a retrieval-only setting. It is outside this audit because none of these checks was applied to it. Its exclusion does not remove it from the literature collection or the separate perspective analysis.

## Numerical analyses

- **SCARE:** reconstruct response counts from rounded published scores and compare coverage, correct answers, and errors.
- **TrustSQL:** check published count/score consistency and report request coverage alongside conditional accuracy.
- **AmbiQT:** inspect reference execution and compare interpretation recovery at fixed candidate budgets.
- **AMBROSIA:** check duplicate references and how output-comparison rules affect gold-query matching.
- **CLARITY:** compare query alternatives derived from annotations, with explicit exclusions and checks of source-table contents. We obtained the code and dataset from its authors. The [replay guide](../analysis/clarity/README.md) links the later public release and its checked revision.

See [analysis instructions](../analysis/README.md) for code, pinned inputs, and scope.
