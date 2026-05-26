# DSL 3.0 Roadmap And Completion Record

Date: 2026-05-09

DSL 3.0 is the post-2.0 capability train. Its purpose is not to make the DSL
larger for its own sake. Each increment must make a new class of realistic web
behavior public, compilable, executable by the evaluator, and fair to blind
candidate implementations that only receive the contract.

## Versioning Rule For The 3.0 Train

Major feature bands move the minor version by `0.1`, and concrete development
increments move the patch version by `0.0.1`.

Every increment must include:

- compiler support and version gating;
- evaluator/web-bridge support when behavior reaches the browser;
- regression validation for prior DSL targets;
- at least one new target or new scenarios that exercise the new feature;
- reference evaluation evidence;
- blind implementation evaluation when the feature is mature enough to be a
  meaningful candidate-generation test;
- documentation of what became expressible and what remains out of scope.

## Completed Bands

| Boundary | Capability | Representative Target |
|---|---|---|
| `2.1.0` | Browser lifecycle and persistence: reload, direct route entry, back/forward, declared persistence scopes. | `case_note_persistence_dsl`, `permit_history_lifecycle_dsl` |
| `2.2.0` | Actor/session scenarios over public shared state. | `radiology_handoff_dsl` |
| `2.3.0` | Deterministic service fixtures and request/response assertions. | `pharmacy_prior_auth_service_dsl` |
| `2.4.0` | Event streams and deterministic background event schedules. | `cold_chain_event_console_dsl` |
| `2.5.0` | Runtime table/grid capture and table-level assertions. | `flight_turnaround_grid_dsl` |
| `2.6.0` | Upload/file input actions. | `expense_batch_upload_dsl` |
| `2.7.0` | Declared normalization and format-insensitive assertions. | `vendor_contact_normalization_dsl` |
| `2.8.0` | Public conflict branches for optimistic-concurrency style workflows. | `inventory_commit_conflict_dsl` |
| `2.9.0` | Cross-collection join projections. | `clinical_case_roster_join_dsl` |
| `3.0.0` | Release boundary with typed upload file schemas and integrated regression evidence. | `claims_review_release_dsl` |

## Current Boundary: 3.0.0

`3.0.0` is a public-release-candidate language boundary for deterministic
web-application behavior that can be expressed through public contracts,
scenario-created values, browser-visible actions, service/event fixtures,
runtime tables, typed uploads, normalization rules, conflict branches, and
join projections.

New release-boundary surface:

- upload actions may declare `file_schema` for CSV fixtures, including column
  names and `string` / `number` / `boolean` types;
- the evaluator and blind-generation prompt treat typed file data as public
  contract, not scenario-only hidden knowledge;
- all 2.x train capabilities remain version-gated and compile under the 3.0
  boundary.

## Validation Evidence

Latest validation at the 3.0 boundary:

- compiler tests: `91 passed`
- compile regression: 46 DSL targets compiled successfully
- focused reference browser regression: 11/11 seed DSL-3 targets passed
- `claims_review_release_dsl` reference evaluation: passed `25/25`
- `claims_review_release_dsl` GPT-5.4 blind evaluation after `file_schema`:
  passed `25/25`

Focused reference regression targets:

- `case_note_persistence_dsl`
- `permit_history_lifecycle_dsl`
- `radiology_handoff_dsl`
- `pharmacy_prior_auth_service_dsl`
- `cold_chain_event_console_dsl`
- `flight_turnaround_grid_dsl`
- `expense_batch_upload_dsl`
- `vendor_contact_normalization_dsl`
- `inventory_commit_conflict_dsl`
- `clinical_case_roster_join_dsl`
- `claims_review_release_dsl`

## Fairness Lesson At 3.0

The first `claims_review_release_dsl` blind run exposed a contract fairness gap:
CSV upload scenario rows contained numeric values, but the public contract did
not declare file column types. A candidate that parsed CSV values as strings
failed join/table expectations that expected numbers.

That failure was not accepted as a model failure. The fix was to add typed
`file_schema` to upload components and version-gate it at `2.9.1` and newer,
then rerun:

- compiler tests still passed;
- the reference app still passed;
- the regenerated GPT-5.4 blind app passed.

The lesson is general: if a scenario relies on normalization, parsing,
conversion, identity, branch, or projection behavior, the rule must be visible
in the public contract.

## Remaining Out Of Scope

DSL 3.0 is still not a universal UI behavior language. Important remaining
gaps include:

- rich cell editing, virtualized grids, pagination, and keyboard grid
  navigation;
- true simultaneous browser contexts and race scheduling beyond deterministic
  actor sequencing;
- drag/drop, sliders, rich text editing, downloads, IME/composition, and focus
  order;
- multi-hop relational graphs and declarative referential-integrity constraints;
- visual-only canvas/spatial/3D applications without public semantic state;
- stochastic or adaptive AI behavior unless the seed and outputs are public;
- hidden backend authorization that has no public state, audit log, or service
  trace.

These are candidates for the next major train, not requirements smuggled into
private scenarios.
