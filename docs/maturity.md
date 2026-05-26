# Benchmark Maturity

This document records how DetoxBench should mature from a working prototype
into a benchmark that can be trusted for candidate comparison. The companion
document `docs/evaluator-stabilization.md` describes the iterative method for
measuring and reducing evaluator error.

## Current Assessment

DetoxBench main is now a DSL-first benchmark prototype. The previous hand-built
web target suite has been removed from main. The surviving target set is defined
by `contract.dsl.yaml`, `scenarios.dsl.yaml`, generated/handwritten reference
apps, and the compiler-backed `evaluate-dsl` runner.

This is a meaningful maturity increase:

- candidate apps receive the public contract, not the scenario file;
- the evaluator compiles actions and assertions from DSL operations;
- target-specific oracle logic is not required for the current DSL suite;
- each browser step captures public state, screenshots, assertions, progress,
  and first-failure metadata;
- dashboards and gallery pages can compare latest run artifacts;
- reference apps can now be productized into domain-specific end-user surfaces
  while preserving the DSL contract boundary;
- scores now include diagnostic stepwise progress, contract-surface failures,
  capability/tier progress, and failure-breakdown metadata in addition to the
  formal scenario score.

It is still not a publication-grade benchmark. The main gap is benchmark
difficulty and release governance, not basic evaluator execution. GPT-5.4 blind
implementations still pass many DSL targets, including the Claim Frontier
family, the first DSL 1.1 multipage target, the first DSL 1.2 async lifecycle
target, the first DSL 1.3 dynamic row-action target, and the first DSL 1.4
bulk-operation target. The first DSL 1.5 structured validation target produced
a narrower GPT-5.4 blind failure on public value-template sequencing. The first
DSL 1.6 nested collection target passed under GPT-5.4, adding fairness evidence.
The first DSL 1.7 logical-time target also passed under GPT-5.4, adding
deterministic schedule coverage. The first compact DSL 2.0 role/session target
passed under GPT-5.4, but the later DSL 2.0 failure-frontier family produced
4/10 blind failures, including three catastrophic 1/20 scores. That is the
first broad evidence that composed DSL 2.0 targets can expose serious model
implementation failures while staying contract-fair.

This does not block paper writing. The current system is strong enough for a
method-oriented draft: Introduction, Related Work, and Method can be written
now. What remains provisional is the benchmark-release claim: final rankings,
stable model-cohort conclusions, and evaluator error-rate estimates. See
`docs/paper-readiness.md`.

## Current Suite Snapshot

The checked-in product suite now contains only the maintained paper-facing
targets:

- `targets/web/stayflow_concierge/tier_a`
- `targets/web/stayflow_concierge/tier_b`
- `targets/web/stayflow_concierge/tier_c`
- `targets/web/freshcart_market/tier_a`
- `targets/web/freshcart_market/tier_b`

Earlier DSL language-growth targets and frontier probes are retained only as
historical documentation, not as runnable checked-in target directories.

The Claim Frontier experiment compiled and evaluated 10 increasingly dense
insurance claim adjudication targets. All reference implementations passed, and
all GPT-5.4 blind implementations also passed. The hardest target reached 28
scenarios, 302 authored DSL action steps, and 604 evaluator logged steps.

This means the current benchmark is strong enough to validate the DSL compiler,
artifact model, and fairness boundary. It now has an initial GPT-5.4 failure
frontier under DSL 2.0 and a broader DSL 3.0 release-candidate language surface,
but the frontier is not yet calibrated enough for a public benchmark release.

The reference-app presentation layer has also improved. The checked-in DSL
targets no longer need to look like raw state dashboards: 35 reference apps were
productized and then rerun through the evaluator, with all reference scenarios
passing. This is a usability/readability improvement, not a change to the
formal behavioral contract.

The multipage experiment adds evidence that browser-visible navigation can be
made part of the public contract and evaluated without reference-only routing
logic. It is a capability increase, not yet a difficulty breakthrough.

The async lifecycle experiment adds evidence that pending and completion states
can be declared and scored without evaluator-private sleeps. It also exposed a
useful authoring lesson: async delays must create an observable public pending
window, and completion effects must leave the app in a declared next state.

The dynamic row-action experiment adds evidence that row-local DOM targeting can
be part of the public contract. It is a capability increase: GPT-5.4 still
passed the first target, but the evaluator now verifies that scenario-created
row identity drives both the clicked selector and the updated public collection
item.

The bulk-operation experiment adds evidence that multi-item updates and removals
can be checked as public ordered-array relations. GPT-5.4 still passed the first
target, but the evaluator now verifies partial bulk commands, all-match
updates, all-match removals, and preservation of non-matching rows.

The structured-validation experiment adds evidence that field error maps can be
scored as public object state. GPT-5.4 passed the validation-key scenarios but
failed later submission scenarios by using zero-based sequence values where the
contract declared `after_path: vendor_count`; this is a useful true failure, not
an evaluator-private rule.

The nested collection experiment adds evidence that parent-scoped child updates,
child removals, nested counts, and nested sums can be scored from public arrays.
GPT-5.4 passed the first compact target, so the semantic boundary is fair but
will need more state-space pressure to become difficult.

The logical-time experiment adds evidence that staged schedule transitions can
be scored without wall-clock time or hidden scheduler state. GPT-5.4 passed the
first compact target, so schedule semantics are now fair infrastructure rather
than a proven difficulty frontier.

The role/session experiment adds evidence that permission-gated actions can be
scored without hidden policy code. Unauthorized attempts remain clickable and
produce public `unauthorized_effects`. GPT-5.4 passed the first compact target,
so role semantics are now fair infrastructure rather than a proven difficulty
frontier.

The DSL 2.0 failure-frontier experiment composes role/session semantics with
page routing, exact action/history accounting, logical time, validation maps,
nested checks, bulk transitions, and collection transfer. All 10 reference apps
passed, while GPT-5.4 blind implementations passed 6/10 and failed 4/10. Three
failures collapsed to 1/20 because redundant navigation double-counted public
actions; one collapsed to 5/20 because page navigation updated history without
changing browser-visible page state. These are fair public contract failures
and should become known-bad calibration fixtures.

The DSL 3.0 train has now reached the `3.0.0` release-candidate language
boundary. The train adds browser lifecycle, actor-scoped execution,
deterministic service fixtures, deterministic event streams, runtime tables,
upload/file input, declared normalization, conflict branches, join projections,
and typed upload schemas. The 3.0 boundary is backed by compiler tests, compile
regression across the checked-in DSL targets, focused browser regression across
the new seed targets, and a GPT-5.4 blind rerun of the integrated claims target
after a file-schema fairness gap was fixed.

The first Target-level RC batch is now managed separately from the broad DSL
testbed. `targets/web/suites/paper-rc.yaml` selects four realistic DSL 3.0
targets for Paper-suite RC promotion: FreshCart Market Ops, HarborStack
Terminal Release Command, GridOps Storm Restoration Board, and Meridian Claims
Adjudication Workspace. Their reference apps pass private scenarios, and each
has GPT-5.4, Claude Opus 4.6, and Gemini 3.1 Pro Preview blind evidence.
Known-bad fixture reports and non-reference parity implementations are present
for all four, and the first paper-grade failure table is recorded in
`docs/paper-suite-rc4-failure-analysis.md`. They should still be treated as RC
evidence rather than publication-complete because GridOps has a deferred
`screenshot_timeout` classification audit, Meridian Claims has a 40-private
scenario shape, and the passing parity fixtures are not yet true clean-room
independent implementations.

## Maturity Levels

Use these levels when deciding whether a target is experimental, usable, or
ready for release.

### Level 0: Sketch

- App idea exists.
- Contract, scenarios, compiler support, evaluator run, or reference app may be
  incomplete.
- Failures are useful only for design discussion.

### Level 1: Compilable Prototype

- `contract.dsl.yaml` and `scenarios.dsl.yaml` compile.
- A reference app runs under `evaluate-dsl`.
- Each step captures state and screenshots.
- Candidate source layout is unrestricted.

This proves the target shape, but not fairness or difficulty.

### Level 2: Fair Internal Target

- Candidate generation receives only the public contract and app description.
- No scenario file is shown to the candidate builder.
- Every scoring assertion is derivable from the DSL contract and
  scenario-created inputs.
- Blocked and rejected behavior is explicit in the contract.
- Scenario tiers are present and cover smoke, behavior, journey, and
  adversarial pressure where meaningful.
- The dashboard shows step-level progress and first failure reason.

This is the first level where candidate failures can be treated as meaningful
internal data.

### Level 3: Calibrated Benchmark Target

- Multiple blind candidate apps have been generated across models, seeds, and
  implementation styles.
- Known-bad subjects exist for common failure modes.
- At least one alternative non-reference implementation passes all scoring
  scenarios, or the target is compiler-generated with independently verified
  semantics.
- Scenario difficulty is calibrated so failures are neither only wiring errors
  nor only massive early journey failures.
- Failure taxonomy is recorded consistently.
- Scoring weights are documented.

This level is suitable for serious internal comparison.

### Level 4: Release Candidate

- DSL version and target version are frozen.
- Public/development, private scoring, and diagnostic probe scenarios are
  separated.
- Private scenarios are reviewed against the public contract before release.
- Candidate prompts, model versions, and run metadata are reproducible.
- Model cohort manifests record repeatable candidate-generation conditions.
- Known-bad fixtures verify that the evaluator catches established defect
  classes.
- Artifacts can be regenerated from a clean checkout.
- The suite gallery can summarize all release targets.

In project terminology, a Target-level RC means a target has reached this level
locally. A Paper-suite RC means the target is also selected into a frozen
paper-facing subset and is being tracked against the publication evidence
gates in `docs/paper-suite-rc.md`.

### Level 5: Public Benchmark

- Target set is frozen for a release version.
- Score computation is stable and documented.
- Regression tests guard compiler, evaluator, dashboard, and gallery behavior.
- Dataset governance is clear: what is public, what is private, what is
  diagnostic, and when a target version changes.
- Report generation distinguishes formal failures from contract-gap findings.
- Known-bad fixtures and model cohorts are part of release regression, not
  ad-hoc experiments.

## Current Gaps

The strongest parts of the project are compiler-backed execution and
observability. The weak points are still difficulty, conformance breadth, and
release governance. DSL 3.0 closes several post-2.0 gaps, but it remains a
release-candidate language boundary rather than a fully governed public
benchmark release. The historical DSL 2.0 gap analysis and post-3.0 status are
tracked in `docs/dsl-v200-gap-analysis.md`.

### Benchmark Difficulty

Risk: A fully public transition contract can be implemented as a small state
machine, especially by a strong model.

Improvement:

- design targets with nested collections, joins, bulk partial operations,
  field-level validation maps, undo/redo stacks, live view-row actions,
  asynchronous request lifecycles, and role/session-specific workflows;
- create larger model/seed cohorts;
- track whether failures are UI contract failures, semantic transition
  failures, or output-size/architecture failures.

### Contract Completeness

Risk: A scenario may accidentally test behavior that was not written into the
public contract. That makes a candidate failure unfair.

Improvement:

- strengthen compiler checks for scenario-to-contract references;
- require every normalization rule, rollback rule, tie-break rule, formula, and
  identity rule to appear in the contract;
- keep contract-gap probes out of formal score.

### Scenario Validity

Risk: Long scenarios can become reference-specific scripts rather than
contract-derived behavioral tests.

Improvement:

- mark every scenario as scoring or diagnostic before release;
- prefer formula, relation, changed/unchanged, blocked, and rejected assertions
  that are derived from public DSL operations;
- make scenario-created values explicit and inspectable.

### Evaluator Error

Risk: The evaluator may fail a conforming implementation, or pass a broken one.

Improvement:

- run blind cohorts repeatedly;
- classify each failed first step as candidate bug, contract gap, evaluator
  overfit, evaluator bug, ambiguous, or accepted pass;
- track false positive rate and known-bad detection rate;
- rerun reference apps after evaluator changes.

### Release Operations

Risk: A benchmark can be locally impressive but hard to reproduce.

Improvement:

- keep generated candidate directories out of the core suite;
- document exact commands for compile, reference evaluation, candidate
  evaluation, dashboard generation, and gallery generation;
- maintain a broad testbed manifest at `targets/web/suite.yaml` and a separate
  paper-facing manifest at `targets/web/suites/paper-rc.yaml`;
- require clean-checkout regeneration before release tags.

## Recommended Next Steps

1. Treat DSL 3.0 as the current mainline capability baseline and avoid
   target-specific evaluator code.
2. Seek a stronger GPT-5.4 failure frontier by composing the full 3.0 surface:
   pages, actors, services, events, tables, uploads, normalization, conflicts,
   joins, validation maps, nested data, logical time, and permissions.
3. Preserve the Claim Frontier and first 2.0 role/session results as negative
   evidence: more scenarios over clear primitives does not automatically create
   harder benchmarks.
4. Expand known-bad generation for DSL targets so false negatives are visible.
5. Add scenario-public/private packaging rules before any public release.
6. Treat release readiness as a governance problem as much as an implementation
   problem.
7. Continue replacing dashboard-like reference surfaces with plausible
   end-user product surfaces, and always rerun full reference regression after
   doing so.

## Release Rule

A DetoxBench release should never score hidden behavior. It may hide scenario
order, scenario data, assertion values, and private workflows, but it must not
hide requirements. If a requirement is not in the public contract, failures
against that requirement are diagnostic findings, not benchmark scores.
