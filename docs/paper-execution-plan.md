# Paper Execution Plan

Date: 2026-05-09

This document turns the paper-readiness discussion into an execution checklist.
The goal is to move DetoxBench from a strong method prototype to a defensible
benchmark paper without weakening the evidentiary bar.

## Target Paper Shape

The first serious manuscript should be framed as a benchmark-method paper:

- `Introduction`: why LLM-generated apps need behavioral conformance
  evaluation, not only visual inspection, code review, or fixed-output tests.
- `Related Work`: web-agent benchmarks, software-engineering benchmarks, UI
  interaction environments, and how DetoxBench differs.
- `Method`: contract DSL, scenario DSL, compiler, evaluator, reference/blind
  implementations, logs, screenshots, scoring, and failure taxonomy.
- `Experiments`: conservative evidence that the method is executable,
  fair-auditable, and capable of surfacing model failures.
- `Limitations`: DSL scope, deterministic/public-state boundary, release
  governance not yet equivalent to a large public leaderboard unless the
  checklist below is completed.

## Minimum Materials

### A. Thesis And Scope

Status: mostly ready.

Needed artifacts:

- one-paragraph thesis;
- precise benchmark scope;
- non-goals;
- definition of "behavioral conformance" for generated apps;
- explanation of why hidden scenario values are allowed but hidden
  requirements are not.

Acceptance criterion:

- A reader can tell DetoxBench apart from web-agent task-completion benchmarks
  and from SWE-style code-repair benchmarks in under one page.

### B. Related Work Map

Status: ready for draft, needs citation polish.

Required clusters:

- web interaction environments: MiniWoB++ style tasks;
- grounded shopping/web tasks: WebShop;
- general web-agent datasets: Mind2Web;
- realistic web-agent environments: WebArena, VisualWebArena;
- enterprise UI agent benchmarks: WorkArena and BrowserGym;
- broader agent benchmarks: AgentBench and OSWorld;
- software engineering benchmarks: SWE-bench.

Acceptance criterion:

- Related Work explains that DetoxBench evaluates generated application
  implementations against public behavioral contracts, while most nearby work
  evaluates agents operating existing environments or fixing existing code.

### C. DSL 3.0 Method Description

Status: ready.

Needed artifacts:

- DSL grammar/shape overview;
- supported behavior classes through DSL 3.0;
- versioning policy;
- compiler validation guarantees;
- examples of contract, scenario, compiled plan, and assertion result.

Acceptance criterion:

- Method can be understood without reading source code.

### D. Target Suite Freeze

Status: target-level RC subset selected; paper-suite evidence incomplete.

Needed artifacts:

- a selected DSL 3.0 paper subset, likely 12 to 20 targets at first;
- target cards describing domain, DSL features, scenario counts, and intended
  failure pressure;
- public/private scenario split for each release target;
- target version ids.

Acceptance criterion:

- The paper can name an exact benchmark suite version, and that suite can be
  regenerated from a clean checkout.

Current concrete subset:

- `freshcart_market_ops_dsl`
- `port_terminal_release_command_dsl`
- `grid_outage_recovery_command_dsl`
- `claims_adjudication_workspace_dsl`

These four are recorded in `targets/web/suites/paper-rc.yaml` and tracked in
`docs/paper-suite-rc.md`. They are Target-level RCs promoted into the
Paper-suite RC workstream, not yet publication-complete benchmark targets.

Current product-realism pilot:

- `targets/web/stayflow_concierge/tier_a`
- `targets/web/stayflow_concierge/tier_b`

StayFlow Concierge Tier A is now the first target built around the newer
paper-target method: realistic commercial UI/UX, DSL 3.0 public contract,
tiered scenarios, a passing productized reference app, and a model ladder from
lower-capability blind implementations to frontier blind implementations. The
method is recorded in `docs/paper-target-development-method.md`; target-specific
results are recorded in `targets/web/stayflow_concierge/tier_a/README.md`.

StayFlow Concierge Tier B is a separate follow-on target with ordered
multi-city itinerary state, quote and promo services, traveler manifest upload,
agent checklist release controls, and 29 passing reference scenarios. Its
target-specific record is `targets/web/stayflow_concierge/tier_b/README.md`.

### E. Reference And Independent Evidence

Status: partial.

Needed artifacts:

- reference app pass for every paper target;
- at least one independent non-reference passing implementation for
  representative targets;
- screenshots/galleries showing realistic productized reference surfaces;
- regression script that reruns the selected subset.

Acceptance criterion:

- The evaluator is not merely fitted to one reference implementation style.

### F. Known-Bad Fixtures

Status: early.

Needed artifacts:

- 3 to 5 known-bad fixtures per representative target;
- manifest of intended failure categories;
- known-bad detection report;
- at least one fixture per recurring failure class.

Recurring classes:

- missing state probe;
- wrong selector/actionability;
- wrong numeric formula or derived state;
- skipped page navigation;
- invalid validation map;
- partial bulk update;
- broken nested/relational identity;
- hidden disabled control for blocked/rejected/unauthorized/conflict action;
- wrong upload parsing or normalization.

Acceptance criterion:

- The evaluator demonstrably catches known defects and reports the intended
  failure class.

### G. Blind Model Cohorts

Status: partial.

Needed artifacts:

- cohort manifests for GPT-5.4 and at least two other model families;
- multiple seeds or regeneration attempts per model/target;
- stored generation metadata: model id, prompt hash, contract hash, git commit,
  response id when available;
- consistent candidate-generation prompt template.

Acceptance criterion:

- Results are not a single-model anecdote.

### H. Evaluator Error Analysis

Status: method ready, data incomplete.

Needed artifacts:

- failure classification table;
- false-positive estimate;
- known-bad detection rate;
- scenario pass rate by tier;
- stepwise progress by tier;
- scenario pass rate by difficulty;
- stepwise progress by difficulty;
- count of contract gaps fixed during stabilization;
- count of scoring assertions moved to probes.

Acceptance criterion:

- The paper can say how often DetoxBench itself was wrong or ambiguous during
  stabilization, not only how often models failed.

### I. Scoring And Reporting

Status: mostly implemented, needs paper tables.

Needed artifacts:

- formal score definition;
- stepwise progress definition;
- tier/capability breakdown;
- difficulty breakdown for comparing weaker and stronger model cohorts;
- UI contract failure count;
- semantic failure count;
- examples of first-failure reports and screenshots.

Acceptance criterion:

- Score interpretation is transparent and does not collapse everything into
  only pass/fail.

### J. Reproducibility Package

Status: partial.

Needed artifacts:

- exact commands for compile, reference evaluation, known-bad evaluation,
  candidate generation, candidate evaluation, dashboard/gallery generation;
- pinned dependencies or environment note;
- release manifest;
- artifact policy for what is checked in vs regenerated.

Acceptance criterion:

- A reviewer can rerun the core paper subset from a clean checkout.

## Recommended Attack Order

1. Freeze a paper subset of DSL 3.0 targets. Status: initial RC4 subset
   selected in `targets/web/suites/paper-rc.yaml`.
2. Split public/private scenarios for that subset.
3. Add known-bad fixtures for 3 representative targets.
4. Build one independent passing implementation for those same targets.
5. Run a first model cohort across the subset.
6. Classify failures and fix unfair checks.
7. Regenerate the cohort after contract/evaluator fixes.
8. Expand known-bad and independent evidence to the rest of the subset.
9. Produce aggregate tables and plots.
10. Draft Introduction, Related Work, and Method in parallel with the evidence
    work, then fill Results only after the cohort/failure analysis stabilizes.

## First Concrete Pilot

The first paper-readiness pilot is intentionally single-target, not a broad
suite freeze. The selected target is `claims_review_release_dsl` because it
combines typed upload, join projection, normalization, conflict semantics,
reload persistence, and table assertions inside the DSL 3.0 boundary.

Pilot tracking document:

- `docs/paper-pilot-claims-review.md`

This pilot has now produced the full first evidence loop: public/private split,
reference pass, independent pass, known-bad fixtures, three-family blind model
cohort, failure taxonomy, and reproducibility commands. The next step is to
scale the same process to more targets and add more scenario pressure.

The first four-target paper-suite RC batch has now completed that same evidence
loop for FreshCart Market Ops, HarborStack Terminal Release Command, GridOps
Storm Restoration Board, and Meridian Claims Adjudication Workspace. The RC4
manifest and cohort are in `targets/web/suites/paper-rc.yaml` and
`cohorts/paper-suite-rc4.yaml`; the consolidated failure table is
`docs/paper-suite-rc4-failure-analysis.md`. Remaining RC caveats are narrower:
GridOps screenshot-timeout classification, Meridian's 40-private-scenario
shape, and replacement of parity fixtures with true clean-room independent
implementations.

## First Three Concrete Tasks

1. Complete the single-target paper pilot. Status: done for
   `claims_review_release_dsl`.

   Output: `docs/paper-pilot-claims-review.md` plus run evidence for
   `claims_review_release_dsl`.

2. Pick 3 representative stabilization targets.

   Candidate next set after the single-target pilot:

   - `claims_review_release_dsl`: integrated DSL 3.0 surface;
   - `inventory_commit_conflict_dsl`: conflict semantics;
   - `clinical_case_roster_join_dsl`: relational/join projection semantics.

   Output: public/private split, known-bad fixture plan, independent-app plan.

3. Define the first cohort manifest. Status: done for the pilot target.

   Output: `cohorts/paper-pilot-claims-review.yaml`, covering GPT-5.4,
   Claude Opus 4.6, and Gemini 3.1 Pro Preview with a fixed prompt template
   hash and contract hash.

## Paper Writing Parallel Track

These sections can be drafted before the full experiment finishes:

- title and abstract sketch;
- Introduction;
- Related Work;
- Method;
- Threats to Validity outline;
- Limitations.

The Results section should wait until the paper subset, known-bad fixtures, and
model cohort runs are stable.
