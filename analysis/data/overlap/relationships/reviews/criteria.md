# Human review criteria


G — Information flow: does the source document one perspective's information affecting a mechanism/output/decision involving the other within this setting? P requires explicit dependency evidence. Shared inputs, a shared encoder, coexistence of labels, or the same benchmark are insufficient alone. N is bounded by the inspected protocol, U means insufficient/access-limited evidence.

E — Empirical relationship evaluation: do reported results analyze a relationship between the two perspectives? Judge E independently of G. A conditional table, explicit cross-diagnostic confusion analysis, controlled comparison, ablation, or inspected-case analysis can qualify. A causal effect is not required. A paper can study diagnostic relationships without implementing separate components or information flow. Conversely, an integrated pipeline can lack such evaluation.

Separate marginal metrics, class-by-class accuracy/F1 without a linked comparison, a single overall task score, or merely including both ambiguity and unanswerability labels do not by themselves qualify E. A source-supported N for G must never automatically set E=N. E=P does not require G=P. Findings reported only in a separate evaluation setting must not be imported.

## Types of evidence (record explicitly)
For IB:
- per_meaning_answerability: the study checks whether individual represented meanings of the same request can be answered with the permitted information, or varies required resources across those meanings.
- request_level_relation: the study links ambiguity/interpretation properties to answerability or missing resources at request level, without a per-meaning assessment.
- diagnostic_confusion: the study explicitly measures or inspects ambiguity-versus-unanswerability classification confusions or the boundary between those diagnostic categories. This concerns recognition of categories and must not be reported as per-meaning feasibility.
Record the supported types, which can overlap. Do not claim per-meaning evidence from a confusion matrix.

For BV controls, record whether feasibility/category conditions are linked to SQL correctness, errors, returned-answer reliability, or verifier behavior. Independent class scores without a linked analysis are insufficient. For the other pairs, apply the same E rule to their established endpoint definitions, retaining the direct-comparison scope of C.

Also describe the diagnostic task as joint prediction, supplied categories, stratified evaluation, no shared diagnostic task, or unclear. This contextual field is not an automatic E decision.

P/N/U are present, absent in the inspected setting, and unclear. Every judgment needs its own rationale and source locators. An inaccessible or uninformative abstract cannot justify an absence claim by silence. If the source supports only a design or tutorial, distinguish that from measured results. Preserve examples with uncertain interpretation validity as evidence of a study target, not certification of their correctness.


## Operational definitions

The endpoint definitions are fixed. I covers possible meanings, ambiguity detection/recovery, or substantive semantic grounding from missing/contextual meaning. Ordinary SQL prediction variation alone is insufficient. B covers whether the request or a represented meaning can be answered using permitted data, schema, knowledge, or tools. Generation failure or confidence alone is insufficient. A covers a studied response or information-selection mechanism (ask, retrieve/inspect, verify/repair, answer/withhold/revise). Fixed generation, supplied completed histories, or fixed extra context alone are excluded. Retrieval qualifies when relevance, ranking, or context selection is studied.

C is direct comparison of outputs within a represented set of readings of the same unchanged request. This includes execution equality used to filter purported redundant readings. Calling equal-result readings paraphrases does not remove that mechanism from scope, but equality does not certify semantic equivalence. Generic sampled SQL candidates, one-correct-parse selection, ordinary reference execution scoring alone, and comparisons of queries intended to express only one meaning are insufficient. Endpoint presence can include a documented design, construction, or illustrated target without certifying implementation or interpretation validity. V is a distinct SQL correctness, equivalence, evaluator, or returned-answer reliability target. Routine task scoring alone is insufficient.

Per-meaning answerability requires checking what each represented meaning needs against permitted resources. Executability or nonempty-result screening during reference construction alone does not establish it. Record such screening explicitly and judge any other relationship separately.

Retain the specified setting: A06::classification covers model category classification with differing cell-value access. Human category annotation is outside that setting and should be recorded as out-of-setting supporting evidence, not imported into its count.

For every IB evidence type, record P/N/U with a rationale. An unselected type is not an absence judgment. Distinguish documented designs from implemented information flow and measured evaluation. Designs or hypothetical examples alone cannot establish E.

