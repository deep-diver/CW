# Behavioral Contract Language Specification

This document defines the rule-based contract language used by the
packaged ConformWeb target files. It is written as a compilation
reference: a contract is valid only when its actions, observations,
scenarios, and checks can be lowered into deterministic browser
evaluation plans.

The document intentionally avoids internal release labels. The packaged
YAML files are the source of truth; this reference explains the
structure and semantics needed to author consistent, compilable
contracts.

## 1. Compilation Model

A target consists of one public contract file and zero or more scenario
files:

```text
contract.dsl.yaml
scenarios.public.dsl.yaml
scenarios.private.dsl.yaml
```

The compiler accepts a scenario only if every referenced action,
selector, state path, role, route, service, event, table, upload schema,
and assertion relation is declared by the public contract. Private
scenarios may hide concrete values, action order, and compositions of
public behavior. They must not introduce new product requirements.

Each executable step is lowered to:

```text
observe_pre -> act -> observe_post -> check
```

The evaluator records public state, browser metadata, service/event
traces, rendered table evidence, and screenshots. Assertions are
rule-based; no language model is used as a judge.

## 2. Contract File Shape

A public contract has the following top-level shape:

```yaml
dsl_version: "<language boundary>"
app:
  id: <target id>
  name: <display name>
  capability: <short capability label>
  ui_ux_brief: <optional product-facing quality brief>
runtime:
  target: web
  state_probe:
    expression: <JavaScript expression returning public state>
  pages: {...}
  session: {...}
  persistence: {...}
  actors: {...}
  services: {...}
  events: {...}
  tables: {...}
state:
  initial: {...}
  schema: {...}
components:
  <component_id>: {...}
```

The compiler treats `state.schema`, `components`, and the relevant
`runtime` declarations as the admissibility boundary for scenarios.

## 3. Public State

`state.schema` is a mapping from public state paths to field types.
Supported field types are:

```text
string, number, boolean, array, object, any
```

`state.initial`, when present, must define every schema path and each
value must match its declared type. Every check that references `path`,
`source_path`, `other_path`, `lookup_path`, or a template state path
must reference a declared schema path. This is what makes later
assertions statically checkable before browser execution.

## 4. Runtime Declarations

`runtime.target` must be `web`.

`runtime.state_probe.expression` defines how the evaluator reads public
state from the browser. The expression must return an object whose
fields match `state.schema`.

`runtime.pages` declares browser-visible routes:

```yaml
runtime:
  pages:
    checkout: {path: /checkout}
    operations: /ops
```

Page paths must begin with `/`. A component may bind to a page, and an
action may declare `navigate_to: <page_id>`. Browser lifecycle scenarios
may also use declared pages.

`runtime.session` declares role state:

```yaml
runtime:
  session:
    role_path: active_role
    roles: [guest, staff, manager]
```

The role path must be a string state path. The initial role must be one
of the declared roles. Actions with `allowed_roles` compile into role
preconditions for normal execution and into an unauthorized branch for
`mode: unauthorized`.

`runtime.persistence.reload` declares reload obligations:

```yaml
runtime:
  persistence:
    reload:
      scope: local_storage
      paths: [cart_items, selected_order_id, active_role]
```

Supported scopes are `local_storage`, `session_storage`, and `url`.
Each path must be a declared state path. Scenarios may use
`browser: reload` only when reload persistence is declared.

`runtime.actors` declares optional named browser actors:

```yaml
runtime:
  actors:
    reviewer: {label: Reviewer, start_page: queue}
    manager: {start_path: /approval}
```

Scenario steps may then include `actor: reviewer`. Actor start pages
must reference declared pages; actor start paths must begin with `/`.

`runtime.services` declares deterministic HTTP fixtures:

```yaml
runtime:
  services:
    quote_service:
      endpoint: /api/quote
      method: POST
      responses:
        - id: accepted
          match:
            body_json: {code: SAVE50}
          status: 200
          json: {credit: 50}
      default_status: 404
```

Methods are `GET`, `POST`, `PUT`, `PATCH`, or `DELETE`. Each response
may match query fields or JSON body fields and must provide `json` or
`text`.

`runtime.events` declares deterministic background or external events:

```yaml
runtime:
  events:
    cold_chain_alert:
      payload: {severity: high}
      preconditions:
        - {op: equals, path: dispatch_status, value: queued}
      effects:
        - {op: equals, path: alert_status, value: active}
```

Event effects are ordinary contract checks evaluated after the event
step.

`runtime.tables` declares rendered table evidence:

```yaml
runtime:
  tables:
    order_grid:
      selector: "[data-table='orders']"
      row_selector: "[data-row-id]"
      row_id_attribute: data-row-id
      source_path: orders
      row_id_field: id
      columns:
        status: "[data-col='status']"
        temp:
          selector: "[data-col='temperature']"
          state_field: temperature
```

Table scenarios may check row order, row count, and individual cell
values. A table column used in a scenario must be declared here.

## 5. Components and Actions

`components` maps public component ids to browser selectors and action
declarations:

```yaml
components:
  add_item_button:
    selector: "[data-testid='add-item']"
    page: catalog
    actions:
      click:
        preconditions:
          - {op: equals, path: current_page, value: catalog}
        effects:
          - {op: changed_by, path: cart_count, by: 1}
```

A component must declare either `selector` or `selector_template`.
`selector_template` may contain `{{input.*}}` tokens and is resolved
using the scenario step input. A component page binding must reference a
declared page.

Supported browser actions are:

```text
click, fill, select, check, uncheck, toggle, upload
```

An action may declare:

- `preconditions`: checks over the before-state;
- `effects`: checks over the after-state for normal execution;
- `blocked_when` and `blocked_effects`;
- `rejected_when` and `rejected_effects`;
- `conflict_when` and `conflict_effects`;
- `allowed_roles` and `unauthorized_effects`;
- `async_effects`;
- `navigate_to`.

Branch declarations must be paired: `blocked_when` requires
`blocked_effects`; `rejected_when` requires `rejected_effects`;
`conflict_when` requires `conflict_effects`. Unauthorized effects
require `allowed_roles`. A blocked, rejected, conflict, or unauthorized
control must remain browser-actionable so the evaluator can observe the
declared public transition.

Upload actions may declare a file schema:

```yaml
actions:
  upload:
    file_schema:
      format: csv
      columns:
        - {name: id, type: string}
        - {name: quantity, type: number}
        - {name: flagged, type: boolean}
    effects:
      - {op: equals, path: uploaded_rows, value_from: input.rows}
```

The only supported file format is CSV. Column types are `string`,
`number`, and `boolean`.

Asynchronous actions declare delayed effects:

```yaml
actions:
  click:
    effects:
      - {op: equals, path: request_status, value: pending}
    async_effects:
      after_ms: 500
      effects:
        - {op: equals, path: request_status, value: complete}
```

A scenario may later use `await: component.action` to wait for the
declared delay and check the delayed effects.

## 6. Scenario File Shape

A scenario file has this top-level shape:

```yaml
dsl_version: "<language boundary>"
visibility: public | private
tier_weights:
  smoke: 1
  core: 2
scenarios:
  - id: private_01_end_to_end
    kind: scoring
    visibility: private
    tier: journey
    difficulty: D
    weight: 3
    steps: [...]
```

`kind` is `scoring` or `probe`; omitted kind defaults to `scoring`.
`visibility` is `public` or `private`; omitted scenario visibility
defaults to `private`. A scenario weight defaults to its tier weight
when present, otherwise to `1.0`. Probe weights may be zero; scoring
weights must be positive.

## 7. Scenario Step Grammar

Component action step:

```yaml
- do: add_item_button.click
  input: {value: lettuce}
  mode: normal
  expect:
    - {op: equals, path: cart_count, value: 1}
```

The `do` field must be `<component_id>.<action>`. The component and
action must be declared in the contract. `mode` defaults to `normal`
and may be `blocked`, `rejected`, `conflict`, or `unauthorized` only
when the action declares the corresponding branch. Scenario `expect`
checks are appended to the action's declared effects.

Upload step:

```yaml
- do: manifest_upload.upload
  input:
    file:
      name: manifest.csv
      mime_type: text/csv
      content: |
        id,name,count
        A-1,Lettuce,3
    rows:
      - {id: A-1, name: Lettuce, count: 3}
```

Browser lifecycle step:

```yaml
- browser: reload
  expect:
    - {op: unchanged, path: cart_items}
- browser: {action: goto, page: checkout}
- browser: back
  expect_page: catalog
```

`reload` requires declared reload persistence. `back` and `forward`
require `expect_page`. `goto` must name a declared page or provide a
path beginning with `/`.

Event step:

```yaml
- event: cold_chain_alert
  expect:
    - {op: equals, path: alert_count, value: 1}
```

Table snapshot step:

```yaml
- table: order_grid
  expect_order: [ORD-1, ORD-2]
  expect_row_count: 2
  expect_rows:
    - id: ORD-1
      cells: {status: approved, total: 42}
```

Wait and asynchronous completion:

```yaml
- wait_ms: 250
  expect:
    - {op: equals, path: status, value: pending}
- await: submit_button.click
  expect:
    - {op: equals, path: status, value: complete}
```

## 8. Value References and Templates

Checks may use literal `value`, `value_from: input.*`, `other_path`, or
template values:

```yaml
- {op: equals, path: guest_name, value_from: input.value}
- {op: relation, path: total_due, operator: ">=", other_path: subtotal}
- op: appended_object
  path: audit_log
  value:
    id: AUD-1
    actor: {from_path: active_role}
    note: {from_input: input.note}
```

`from_path` reads the before-state; `after_path` reads the after-state;
`from_input` reads scenario input. String templates may reference state
paths and `.length` for array or string paths.

## 9. Check Operator Catalog

Basic scalar and relation checks:

- `equals`: after-state path equals `value` or `value_from`;
- `unchanged`: before and after values are equal;
- `changed`: before and after values differ;
- `changed_by`: numeric delta equals `by`;
- `changed_by_path`: numeric delta equals another path times an
  optional multiplier;
- `toggled`: boolean value flips;
- `truthy` / `falsey`: after-state truthiness;
- `relation`: compare path to `value`, `value_from`, or `other_path`
  with a declared operator;
- `one_of` / `not_one_of`: membership over a finite value list;
- `matches`: string path matches a regular expression;
- `contains` / `not_contains`: array or string containment.

String and numeric derivations:

- `equals_template`: render a string template from public state;
- `equals_normalized`: compare after applying declared normalizers;
- `equals_linear`: numeric formula from state terms plus constant;
- `equals_piecewise_linear`: choose a numeric formula by ordered
  public conditions;
- `advanced_time_by`: logical-clock numeric delta.

Collection checks and mutations:

- `appended`: array contains an appended literal or input value;
- `appended_object`: array gains an object built from a value template;
- `removed_first`: first array item is removed;
- `removed_first_where` / `removed_all_where`: remove matching rows;
- `removed_all_where_after`: remove rows using predicates evaluated
  against after-state;
- `updated_first_where` / `updated_all_where`: update matching rows;
- `updated_all_where_after`: update rows using after-state predicates;
- `moved_first_where`: move the first matching row to `to_index`;
- `appended_from_first_where`: copy a matching item from a source
  collection, optionally applying updates;
- `length_changed_by`: array or string length delta.

Object and validation checks:

- `updated_object_fields`: object gains or replaces named fields;
- `removed_object_fields`: object removes named fields;
- `equals_object_key_count`: numeric path equals object key count.

Derived collection projections:

- `equals_length`: numeric path equals array/string length;
- `equals_count_where`: count items matching predicates;
- `equals_any_where`: boolean path equals whether any item matches;
- `equals_sum`: numeric path equals a field sum with optional
  multiplier, constant, and rounding;
- `equals_first_item_field` / `equals_last_item_field`: scalar path
  equals a field from the first/last source item or a default;
- `equals_filter`: array path equals a filtered and optionally sorted
  projection of a source collection;
- `equals_join_projection`: array path equals a projection formed by
  joining a source collection to a lookup collection.

Nested collection checks:

- `updated_first_child_where`: update the first child matching parent
  and child predicates;
- `removed_first_child_where`: remove the first matching child;
- `equals_nested_count_where`: count child rows under matching parents;
- `equals_nested_sum`: sum child fields under matching parents.

Table checks are produced only by table snapshot steps:

- `table_order_equals`;
- `table_row_count_equals`;
- `table_cell_equals`.

## 10. Predicate and Collection Rules

Collection predicates appear in `where`, `parent_where`, and
`child_where`. They are public, declarative filters over item fields
or scenario input. Typical predicates include equality, inequality,
relation comparisons, membership, and `value_from: input.*` binding.
A check that mutates or derives a collection must declare its source
collection explicitly through `path` or `source_path`.

The compiler rejects under-specified collection operations. For
example, `updated_first_where` requires a non-empty `where` and
non-empty `updates`; `equals_count_where` requires a non-empty `where`;
`equals_sum` requires a field name; join projections require source
keys, lookup keys, and projected fields.

## 11. Determinism and Fairness Rules

A contract is fair only if every scoring requirement is derivable from
the public contract. Scenario files may choose values and compose
behaviors; they may not invent selectors, routes, state paths, parsing
rules, role policies, service responses, table schemas, or persistence
obligations.

Candidate generation receives the product premise, the complete public
contract, and the permitted runtime shape. It does not receive held-out
scenarios, reference source code, evaluator traces, screenshots, or
failure feedback.

The language targets deterministic, browser-executable web-app behavior
with a public semantic state interface. It does not score visual taste,
source-code style, hidden backend authorization with no public evidence,
stochastic AI behavior, or canvas/spatial interfaces without declared
semantic observations.
