# Scenario Difficulty Tiers

DetoxBench reports two orthogonal scenario labels:

- `tier`: product capability or failure class, such as `roles`, `history`,
  `service`, `conflict`, or `complex`.
- `difficulty`: model-facing challenge level, used to compare weak, midrange,
  and frontier model cohorts.

The difficulty ladder is derived from the claims adjudication and surgical
authorization targets. It is empirical rather than decorative: each level names
the kind of behavior that actually changed model outcomes during stabilization.

## Difficulty Ladder

### `d1_smoke`

Purpose: verify that the app exposes the public contract surface at all.

Typical checks:

- reset and initial state;
- single navigation or role switch;
- one upload or one direct input;
- simple rendered row count/order;
- one normalization rule.

Expected model behavior: most capable models should pass. A failure here usually
means the candidate missed selectors, state probe shape, routing, or basic file
upload semantics.

### `d2_core`

Purpose: verify one focused product rule or state transition.

Typical checks:

- one service lookup followed by one workflow mutation;
- one conflict or rejected/unauthorized branch;
- one reload-persistence requirement;
- one terminal case transition;
- one derived counter or sum.

Expected model behavior: competent implementations should mostly pass, but
partial DSL interpreters often fail service counters, conflict no-ops, or
precise derived fields.

### `d3_integrated`

Purpose: compose several contract features into a realistic workflow.

Typical checks:

- role changes plus workflow actions;
- multi-actor handoff;
- approval/release staging;
- secondary ledger creation and resolution;
- reload after non-trivial public state has accumulated.

Expected model behavior: models that implemented isolated reducers often begin
to fail here because the same state must remain coherent across multiple
components, pages, roles, and ledgers.

### `d4_adversarial`

Purpose: probe plausible partial implementations and edge ordering.

Typical checks:

- wrong-role no-op storms;
- browser back/forward after state mutation;
- route-crossing events;
- duplicate audit/projection order;
- normalized input plus conflict repair;
- event/conflict precedence.

Expected model behavior: even strong blind candidates frequently pass many
state transitions but fail exact rendered table projection, duplicate event
ordering, or route/history persistence.

### `d5_stress`

Purpose: stress long-horizon, high-density behavior where many public ledgers
must agree.

Typical checks:

- 50+ step end-to-end workflows;
- multiple independent ledgers updated from one journey;
- service calls, events, conflicts, roles, reload, history, and table
  projections in one scenario;
- simultaneous actor pages that must share one public workflow state without
  render/storage feedback loops;
- reset/reupload cleanup after dense state;
- final reconciliation across visible worklist, audit/safety log, packet,
  exception, appeal/review, recovery/turnover, and hold ledgers.

Expected model behavior: frontier models may still complete most early steps,
but failures should reveal where implementation abstractions are incomplete.
The important signal is often the gap between formal pass/fail and stepwise
progress.

## Authoring Rules

- Every release-facing target should include difficulty labels on all scoring
  scenarios.
- A paper-facing target should have at least 10 scoring scenarios per
  difficulty bucket unless it is explicitly a small regression fixture.
- Difficulty should not hide requirements from candidate builders. Requirements
  must remain derivable from `contract.dsl.yaml`; scenarios only choose action
  order and concrete public inputs.
- Raising difficulty should usually increase composition density, not private
  magic. Prefer combining public service, role, route, event, upload,
  persistence, and table projection obligations over inventing evaluator-only
  expectations.
- Report both formal score and stepwise score per difficulty. A high stepwise
  score with low formal score is useful: it means the candidate almost followed
  the journey but failed a specific behavioral contract.

## Current Calibration Targets

- `claims_adjudication_workspace_dsl`: first target that exposed the table
  projection cliff in GPT-5.4 blind candidates.
- `surgical_authorization_command_dsl`: cross-domain replication target with
  52 private scenarios and at least 10 scenarios in each difficulty bucket.
- `grid_outage_recovery_command_dsl`: electric-utility storm restoration target
  with a paper-map field command reference UI, 60 private scenarios, and at
  least 10 scenarios in each difficulty bucket. It currently exposes useful
  GPT-5.4 blind failures on multi-actor page state synchronization, including a
  cross-tab localStorage render/save loop in `blind_gpt54_02`, while the
  reference implementation keeps all public contract probes green.

## Paper Target Tier Expectations

For paper-facing targets, the tier ladder should be used as a design budget, not
as post-hoc decoration:

- `d1_smoke`: at least 10 scenarios that prove selectors, state probe shape,
  upload, route, role, reset, and normalization basics.
- `d2_core`: at least 10 scenarios that each isolate one essential rule, such
  as service lookup, conflict no-op, role gate, terminal transition, or derived
  counter.
- `d3_integrated`: at least 10 scenarios that combine pages, roles, persistence,
  service calls, ledgers, and visible tables.
- `d4_adversarial`: at least 10 scenarios that attack plausible partial
  implementations: wrong-role storms, route crossing, browser history, duplicate
  events, stale drafts, or table projection ordering.
- `d5_stress`: at least 10 long scenarios that force multi-ledger
  reconciliation after dozens of steps.

The target is considered calibrated only when the reference implementation
passes every bucket, a blind candidate is evaluated through the same compiled
evaluator, and the first failure can be classified as either a real candidate
defect or a contract/spec ambiguity.
