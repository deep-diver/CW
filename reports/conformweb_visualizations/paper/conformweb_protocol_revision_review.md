# ConformWeb Protocol Draft Self-Review

This review scores the current draft against the intended positioning:
ConformWeb should read as a contract-grounded evaluation protocol for
LLM-generated web applications, with the scenario collection serving as an
empirical instantiation rather than the primary novelty claim.

Scoring convention:
- Completeness: 10 means ready to survive a top-tier methods/benchmark review on positioning and clarity.
- Reject-risk pressure: 10 means high risk; lower is better.

## Positioning Checks

- The abstract defines ConformWeb first as an evaluation protocol, not as a benchmark collection.
- The central novelty is stated as a public behavioral contract with three roles: generation input, hidden-scenario admissibility boundary, and source for deterministic browser checks.
- The introduction foregrounds the evaluation-boundary shift: the generated artifact becomes the interactive environment.
- The hidden-evaluation dilemma is explicit: hidden workflows are necessary, but hidden requirements would be unfair.
- The instantiation is described through public/private scenarios and a controlled factorial structure rather than by leading with the number of instances.
- Contributions now follow the intended structure: formulation, ConformWeb protocol, and diagnostic analysis of LLM-generated web app failures.
- Results now include denominator accounting, model capability breakdowns, tier breakdowns, and failure-mix/timing observations rather than a single headline score.
- Method now formalizes the protocol object \(G=M(x,C,P_C)\), admissible private scenarios \(\tau\preceq C\), and compiled evaluator \(E_C=\mathrm{compile}(C,T_C)\).
- The draft now includes a concrete contract-to-private-scenario example and clearer scope language for false negatives, passing results, and static packaging.
- The protocol now anticipates three reviewer questions: how contracts are written, why hidden scenarios are fair, and why rule-based evaluation is not open-ended visual judging.
- Reference implementations are described as executable witnesses, not hidden targets.
- Experiments are framed around the conformance gap and protocol stress tests, not model ranking.
- Error analysis is framed around contract-facing boundary failures rather than source-code style or generic bugs.

## Section Scores After Revision

| Section | Completeness | Reject-risk pressure | Rationale |
|---|---:|---:|---|
| Abstract | 9.2/10 | 3.0/10 | Protocol-first framing is clear; numerical result supports the claim without leading with benchmark scale. |
| Introduction | 9.4/10 | 2.7/10 | Boundary shift is sharper: generated artifact becomes the stateful environment that evaluation must test. |
| Related Work | 9.0/10 | 3.5/10 | Organized by evaluation boundary rather than literature buckets alone. Could improve further with exact citations once bibliography is finalized. |
| Protocol | 9.6/10 | 2.3/10 | The protocol object now distinguishes ConformWeb from ordinary E2E/model-based testing by making the generated artifact the environment and the public contract the shared boundary. |
| Protocol Instantiation | 9.3/10 | 3.0/10 | Reframed around scenario-level evidence and controlled factorial structure; avoids defensive scale language. |
| Experiments | 9.3/10 | 2.9/10 | Results include conformance gap, realized/planned denominator accounting, model scaling, tier coupling breakdowns, and scope defense for strict scoring/static packaging. |
| Error Analysis | 9.3/10 | 3.0/10 | Failure taxonomy is tied to capability scaling and timing, showing which failures remain after surface construction improves. |
| Conclusion | 9.2/10 | 3.1/10 | Ends with the evaluation-boundary claim rather than task-scale framing. |

## Remaining Submission Risks

- The title still contains "Benchmark"; this is acceptable if the abstract and introduction keep the protocol-first framing, but it may still bias some reviewers.
- Instance count should stay in method/details, while the intro should emphasize public/private scenario coverage and protocol validation.
- Related Work will depend on citation precision. The current prose is positioned correctly, but the final bibliography should support the evaluation-boundary contrast.
- The final PDF page budget may force cuts; if cuts are needed, preserve Protocol and the admissibility/conformance figure before trimming model-specific detail.

## Current Overall Judgment

- Overall completeness: 9.5/10.
- Estimated reject-risk pressure from positioning alone: 2.5/10.
- Main remaining reject risk is no longer "just another small benchmark"; it is whether reviewers accept the public-contract protocol as a sufficiently novel evaluation boundary.
