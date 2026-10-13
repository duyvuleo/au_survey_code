# Taxonomy

The four perspectives describe the meaning of a request, the information needed to answer it, differences between answers, and the system's response. A study can contribute to several perspectives.

The reading families below include both direct answer comparison and supporting verification under Consequence. The numerical overlap analysis distinguishes these roles and uses direct comparison for its main counts.

## Interpretation: What does the request mean?

- **Annotate plausible interpretations:** [AmbiQT](https://aclanthology.org/2023.emnlp-main.436/) (2023); [AMBROSIA](https://arxiv.org/abs/2406.19073) (2024).
- **Generate and expand alternatives:** [LogicalBeam](https://aclanthology.org/2023.emnlp-main.436/) (2023); [DFPL](https://aclanthology.org/2025.findings-acl.863/) (2025); [FALCON](https://arxiv.org/abs/2610.03625) (2026, training-data generation).
- **Ground schema and value references:** [TACO](https://arxiv.org/abs/2606.14201) (2026); [VALASQL](https://link.springer.com/chapter/10.1007/978-981-95-6196-4_9) (2026). The VALASQL benchmark tests synonyms and abbreviations that differ from stored database values.
- **Characterize conversational uncertainty:** [CLARITY](https://aclanthology.org/2026.acl-industry.86/) (2026; [code and data](https://github.com/duyvuleo/clarity)); [TIDE-Bench](https://arxiv.org/abs/2608.29543) (2026).

## Answerability: Can each meaning be answered?

- **Classify request status:** [TriageSQL](https://arxiv.org/abs/2010.12634) (2020); [LatentRefusal](https://arxiv.org/abs/2601.10398) (2026).
- **Locate problematic facets:** [NoisySP / DTE](https://aclanthology.org/2023.findings-acl.352/) (2023); [CLARITY](https://aclanthology.org/2026.acl-industry.86/) (2026; [code and data](https://github.com/duyvuleo/clarity)).
- **Ground in supporting context:** [EntSQL](https://arxiv.org/abs/2606.03363) (2026); [BIRD-History](https://arxiv.org/abs/2608.29345) (2026).
- **Evaluate feasibility with correctness:** [SCARE: input SQL](https://proceedings.mlr.press/v297/lee26b.html) (2026); [TrustSQL: generated SQL](https://arxiv.org/abs/2403.15879) (2024).

## Consequence: Do different meanings change the answer?

- **Group observed outcomes:** [RTS++](https://openproceedings.org/2026/conf/edbt/paper-177.pdf) (2026); [PleaSQLarify](https://arxiv.org/abs/2603.01795) (2026).
- **Generate discriminating tests:** [Distilled test suites](https://aclanthology.org/2020.emnlp-main.29/) (2020); [ParSEval](https://www.vldb.org/pvldb/vol18/p4750-miao.pdf) (2025).
- **Verify query equivalence:** [SPOTIT](https://www.cs.sfu.ca/~yuepeng/pubs/iclr26.pdf) (2026); [SpotIt+](https://arxiv.org/abs/2603.04334) (2026).
- **Estimate candidate correctness:** [TraceSQL](https://arxiv.org/abs/2608.17795) (2026); [MRSQLGen](https://matafeiyanll.github.io/paper/FSE26-MRSQLGen.pdf) (2026).
- **Audit risk and evaluators:** [Oracle-sensitive certification](https://arxiv.org/abs/2609.25938) (2026); [SQL judge audit](https://arxiv.org/abs/2609.30290) (2026).

## Action: What should the system do next?

- **Elicit user repair:** [NaLIR](https://www.vldb.org/pvldb/vol8/p73-li.pdf) (2014); [PIIA](https://aclanthology.org/2020.emnlp-main.561/) (2020).
- **Select informative questions:** [SQL-EIG](https://arxiv.org/abs/2507.06467) (2025); [APEL](https://aclanthology.org/2023.emnlp-main.312/) (2023).
- **Acquire context and user history:** [SOMA-SQL](https://arxiv.org/abs/2606.11424) (2026); [LinkedIn SQL Bot](https://arxiv.org/abs/2507.14372v1) (2025).
- **Decide whether to answer:** [RTS](https://arxiv.org/abs/2501.10858) (2025); [RTS++](https://openproceedings.org/2026/conf/edbt/paper-177.pdf) (2026). RTS can stop generation or ask for clarification when schema links are uncertain.
- **Evaluate interactive resolution:** [ABISS](https://arxiv.org/abs/2607.23340) (2026); [TIDE-Bench](https://arxiv.org/abs/2608.29543) (2026).
