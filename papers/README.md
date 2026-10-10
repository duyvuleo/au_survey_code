# Papers

Curated resources for **When Does Ambiguity Matter? A Survey of Ambiguity and Unanswerability in Reliable Text-to-SQL**. The collection contains 64 technical studies and five related surveys. The technical literature cutoff is 05 October 2026. The quantitative analyses retain a fixed corpus with a publication cutoff of 01 October 2026. Links identify the recorded sources, not necessarily their latest versions.

## Contents

- [Interpretation](#interpretation) — 8 studies
- [Answerability](#answerability) — 14 studies
- [Consequence and verification](#consequence-and-verification) — 16 studies
- [Action and interaction](#action-and-interaction) — 15 studies
- [Context and user adaptation](#context-and-user-adaptation) — 10 studies
- [Related surveys](#related-surveys) — 5 surveys

These groups provide a reading order, rather than exclusive scientific assignments. A study can address several perspectives. The [taxonomy guide](taxonomy.md) groups representative method families; the [analysis inputs](../analysis/data/README.md) retain setting-level assignments used for numerical comparisons. IDs are retained to connect papers with those records.

## Interpretation

| Year | Paper | ID |
|---|---|---|
| 2026 | [An Extensible Benchmark for Value Ambiguity Resolution in Text-to-SQL](https://link.springer.com/chapter/10.1007/978-981-95-6196-4_9) | `M07` |
| 2026 | [CLARITY: A Framework and Benchmark for Conversational Language Ambiguity and Unanswerability in Interactive NL2SQL Systems](https://aclanthology.org/2026.acl-industry.86/) · [Code and data](https://github.com/duyvuleo/clarity) | `M05` |
| 2026 | [TACO: A Benchmark for Open-Domain Text-to-SQL with Ambiguous and Cross-Database Queries](https://arxiv.org/abs/2606.14201) | `M06` |
| 2026 | [To RAG or Not to RAG, That Is the Question: Effective Text-to-SQL Generation Under Ambiguity](https://scp.cc.gatech.edu/external-news/ieee-xplore-rag-or-not-rag-question-effective-text-sql-generation-under-ambiguity) | `M08` |
| 2025 | [AmbiSQL: Interactive Ambiguity Detection and Resolution for Text-to-SQL](https://arxiv.org/abs/2508.15276) | `M04` |
| 2025 | [Disambiguate First, Parse Later: Generating Interpretations for Ambiguity Resolution in Semantic Parsing](https://aclanthology.org/2025.findings-acl.863/) | `M03` |
| 2024 | [AMBROSIA: A Benchmark for Parsing Ambiguous Questions into Database Queries](https://arxiv.org/abs/2406.19073) | `M02` |
| 2023 | [Benchmarking and Improving Text-to-SQL Generation under Ambiguity](https://aclanthology.org/2023.emnlp-main.436/) | `M01` |

## Answerability

| Year | Paper | ID |
|---|---|---|
| 2026 | [An OMOP-Based Open-Source Text-to-SQL Benchmark Dataset](https://aclanthology.org/2026.clinicalnlp-1.40/) | `S13` |
| 2026 | [Beyond "I Don't Know": Evaluating LLM Self-Awareness in Discriminating Data and Model Uncertainty](https://arxiv.org/abs/2604.17293) | `S11` |
| 2026 | [EntSQL: A Benchmark for Grounding Text-to-SQL in Long-Context Enterprise Knowledge](https://arxiv.org/abs/2606.03363) | `S09` |
| 2026 | [LatentRefusal: Latent-Signal Refusal for Unanswerable Text-to-SQL Queries](https://arxiv.org/abs/2601.10398) | `S08` |
| 2026 | [Query Carefully Revisited: Detecting Unanswerable Queries in Text-to-SQL Across Datasets and Models in Biomedicine](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6877678) | `S12` |
| 2026 | [SCARE: A Benchmark for SQL Correction and Question Answerability Classification for Reliable EHR Question Answering](https://proceedings.mlr.press/v297/lee26b.html) | `S14` |
| 2025 | [Do not Abstain! Identify and Solve the Uncertainty](https://aclanthology.org/2025.acl-long.840/) | `S10` |
| 2025 | [Query Carefully: Detecting the Unanswerables in Text-to-SQL Tasks](https://arxiv.org/abs/2512.21345) | `S07` |
| 2025 | [SQUAB: Evaluating LLM robustness to Ambiguous and Unanswerable Questions in Semantic Parsing](https://aclanthology.org/2025.emnlp-main.906/) | `S06` |
| 2024 | [Overview of the EHRSQL 2024 Shared Task on Reliable Text-to-SQL Modeling on Electronic Health Records](https://aclanthology.org/2024.clinicalnlp-1.62/) | `S03` |
| 2024 | [TrustSQL: Benchmarking Text-to-SQL Reliability with Penalty-Based Scoring](https://arxiv.org/abs/2403.15879) | `S05` |
| 2023 | [Know What I don’t Know: Handling Ambiguous and Unknown Questions for Text-to-SQL](https://aclanthology.org/2023.findings-acl.352/) | `S04` |
| 2022 | [EHRSQL: A Practical Text-to-SQL Benchmark for Electronic Health Records](https://arxiv.org/abs/2301.07695) | `S02` |
| 2020 | [Did You Ask a Good Question? A Cross-Domain Question Intention Classification Benchmark for Text-to-SQL](https://arxiv.org/abs/2010.12634) | `S01` |

## Consequence and verification

| Year | Paper | ID |
|---|---|---|
| 2026 | [Auditing and Repairing LLM-as-Judge Failures in a Production Text-to-SQL Pipeline](https://arxiv.org/abs/2609.30290) | `C16` |
| 2026 | [Certified Against Which Oracle? Execution Labels Set the Reported Risk of Conformal Abstention for Text-to-SQL](https://arxiv.org/abs/2609.25938) | `C15` |
| 2026 | [Disentangling Ambiguity from Instability in Large Language Models: A Clinical Text-to-SQL Case Study](https://arxiv.org/abs/2602.12015) | `C09` |
| 2026 | [R3-SQL: Ranking Reward and Resampling for Text-to-SQL](https://aclanthology.org/2026.findings-acl.2146/) | `C11` |
| 2026 | [Reliable End-to-End Text-to-SQL Generation](https://openproceedings.org/2026/conf/edbt/paper-177.pdf) | `C08` |
| 2026 | [SpotIt+: Verification-based Text-to-SQL Evaluation with Database Constraints](https://arxiv.org/abs/2603.04334) | `C07` |
| 2026 | [SPOTIT: Evaluating Text-to-SQL Evaluation with Formal Verification](https://www.cs.sfu.ca/~yuepeng/pubs/iclr26.pdf) | `C06` |
| 2026 | [Text-to-SQL Evaluation Toolkit](https://research.ibm.com/publications/text-to-sql-evaluation-toolkit) | `C14` |
| 2026 | [TraceSQL: Traceable Answerability Estimation for Reference-Free Text-to-SQL Verification](https://arxiv.org/abs/2608.17795) | `C10` |
| 2026 | [Validating LLM-Generated SQL Queries through Metamorphic Prompting](https://matafeiyanll.github.io/paper/FSE26-MRSQLGen.pdf) | `C13` |
| 2026 | [What Predicts Correctness in Text-to-SQL? A Selective-Prediction Study](https://arxiv.org/abs/2607.06799) | `C12` |
| 2025 | [Fundamental Challenges in Evaluating Text2SQL Solutions and Detecting Their Limitations](https://arxiv.org/abs/2501.18197) | `C04` |
| 2025 | [ParSEval: Plan-aware Test Database Generation for SQL Equivalence Evaluation](https://www.vldb.org/pvldb/vol18/p4750-miao.pdf) | `C05` |
| 2023 | [Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation](https://arxiv.org/abs/2302.09664) | `C03` |
| 2020 | [Semantic Evaluation for Text-to-SQL with Distilled Test Suites](https://aclanthology.org/2020.emnlp-main.29/) | `C02` |
| 2016 | [Inferring Logical Forms From Denotations](https://aclanthology.org/P16-1003/) | `C01` |

## Action and interaction

PlanPool is discussed in the survey but excluded from the fixed quantitative analyses because it was published after their cutoff.

| Year | Paper | ID |
|---|---|---|
| 2026 | [ABISS: Evaluating Text-to-SQL Systems Through Agent Interaction](https://arxiv.org/abs/2607.23340) | `A11` |
| 2026 | [Beyond Correctness: Resolving Underspecification in Agentic Text-to-SQL](https://arxiv.org/abs/2610.02739) | `PlanPool2026` (literature only) |
| 2026 | [BIRD-INTERACT: Re-imagining Text-to-SQL Evaluation via Lens of Dynamic Interactions](https://proceedings.iclr.cc/paper_files/paper/2026/hash/496b549556509bbb9770bf9d335c5800-Abstract-Conference.html) | `A08` |
| 2026 | [Evaluating LLMs on Conversational Text-to-SQL under Chain Ambiguity and Intent Drift](https://arxiv.org/abs/2608.29543) | `A12` |
| 2026 | [PleaSQLarify: Visual Pragmatic Repair for Natural Language Database Querying](https://arxiv.org/abs/2603.01795) | `A09` |
| 2026 | [SOMA-SQL: Resolving Multi-Source Ambiguity in NL-to-SQL via Synthetic Log and Execution Probing](https://arxiv.org/abs/2606.11424) | `A10` |
| 2026 | [Structured Uncertainty guided Clarification for LLM Agents](https://aclanthology.org/2026.findings-acl.2028/) | `A14` |
| 2026 | [Value of Information: A Framework for Human–Agent Communication](https://aclanthology.org/2026.acl-long.1987/) | `A13` |
| 2025 | [Interactive Text-to-SQL via Expected Information Gain for Disambiguation](https://arxiv.org/abs/2507.06467) | `A07` |
| 2025 | [PRACTIQ: A Practical Conversational Text-to-SQL dataset with Ambiguous and Unanswerable Queries](https://aclanthology.org/2025.naacl-long.13/) | `A06` |
| 2025 | [Reliable Text-to-SQL with Adaptive Abstention](https://arxiv.org/abs/2501.10858) | `A15` |
| 2023 | [Non-Programmers Can Label Programs Indirectly via Active Examples: A Case Study with Text-to-SQL](https://aclanthology.org/2023.emnlp-main.312/) | `A05` |
| 2020 | [“What Do You Mean by That?” A Parser-Independent Interactive Approach for Enhancing Text-to-SQL](https://aclanthology.org/2020.emnlp-main.561/) | `A03` |
| 2019 | [CoSQL: A Conversational Text-to-SQL Challenge Towards Cross-Domain Natural Language Interfaces to Databases](https://aclanthology.org/D19-1204/) | `A04` |
| 2019 | [Model-based Interactive Semantic Parsing: A Unified Framework and A Text-to-SQL Case Study](https://aclanthology.org/D19-1547/) | `A02` |
| 2014 | [Constructing an Interactive Natural Language Interface for Relational Databases](https://www.vldb.org/pvldb/vol8/p73-li.pdf) | `A01` |

## Context and user adaptation

| Year | Paper | ID |
|---|---|---|
| 2026 | [BIRD-History: A Benchmark for History-Driven Text-to-SQL with Fine-Grained Knowledge Annotations](https://arxiv.org/abs/2608.29345) | `PersonaBIRDHistory` |
| 2026 | [Business Logic-Driven Text-to-SQL Data Synthesis for Business Intelligence](https://arxiv.org/abs/2601.14518v1) | `PersonaBusinessLogic2026` |
| 2026 | [Learning Personalized Agents from Human Feedback](https://arxiv.org/abs/2602.16173) | `PA-PAHF` |
| 2026 | [PrefIx: Understand and Adapt to User Preference in Human-Agent Interaction](https://aclanthology.org/2026.findings-acl.1506/) | `PA-PrefIx` |
| 2026 | [TAHOE: Text-to-SQL with Automated Hint Optimization from Experience](https://arxiv.org/abs/2606.12387v1) | `PersonaTahoe2026` |
| 2026 | [UserToolBench: A User-Profile-Hidden Benchmark for Personalized Decision Making in Tool-Use LLMs](https://arxiv.org/abs/2608.10042) | `PA-UserToolBench` |
| 2025 | [ClarifyMT-Bench: Benchmarking and Improving Multi-Turn Clarification for Conversational Large Language Models](https://arxiv.org/abs/2512.21120) | `PA-ClarifyMT` |
| 2025 | [RubikSQL: Lifelong Learning Agentic Knowledge Base as an Industrial NL2SQL System](https://arxiv.org/abs/2508.17590v1) | `PersonaRubikSQL2025` |
| 2025 | [Text-to-SQL for Enterprise Data Analytics](https://arxiv.org/abs/2507.14372v1) | `PersonaLinkedIn2025` |
| 2024 | [Sphinteract: Resolving Ambiguities in NL2SQL Through User Interaction](https://www.vldb.org/pvldb/vol18/p1145-zhao.pdf) | `PA-Sphinteract` |

## Related surveys

| Year | Paper | ID |
|---|---|---|
| 2025 | [A Survey of Text-to-SQL in the Era of LLMs: Where Are We, and Where Are We Going?](https://arxiv.org/abs/2408.05109) | `L01` |
| 2025 | [A Survey on Employing Large Language Models for Text-to-SQL Tasks](https://doi.org/10.1145/3737873) | `SurveyShi2025` |
| 2024 | [Natural Language Interfaces for Tabular Data Querying and Visualization: A Survey](https://arxiv.org/abs/2310.17894v3) | `SurveyZhang2024` |
| 2022 | [Recent Advances in Text-to-SQL: A Survey of What We Have and What We Expect](https://aclanthology.org/2022.coling-1.190/) | `L02` |
| 2019 | [A comparative survey of recent natural language interfaces for databases](https://link.springer.com/article/10.1007/s00778-019-00567-8) | `SurveyAffolter2019` |
