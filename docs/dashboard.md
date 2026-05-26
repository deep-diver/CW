# Dashboard Design

The DetoxBench dashboard is a static comparison view over DSL evaluator run
artifacts.

## Goals

- Compare multiple implementations on the same scenarios at a glance.
- Show pass/fail status by scenario, tier, and subject.
- Keep every step inspectable with before/after screenshots.
- Surface failed assertions and state diffs without requiring manual JSONL
  reading.
- Show step-level progress, including where each scenario first failed and why.
- Work from generated artifacts only, without a database or web backend.

## Data Source

The dashboard scans:

```text
targets/web/<suite>/<tier>/cohorts/**/summary.json
```

Only the latest `run_id` per subject is included in the rendered dashboard.
Older artifacts may remain on disk for audit/debugging, but they do not appear
in the comparison UI.

Each summary contains:

- scenario results
- tier metadata
- formal, stepwise, capability, contract, and failure-breakdown score summaries
- step results
- before/after public state
- assertion results
- screenshot paths
- expected, completed, and passed step counts
- first failure metadata, including failed assertion details or scenario errors

The dashboard also reads `<target>/scenarios.dsl.yaml` when present. This lets
it recover scenario labels, tiers, and expected step counts even for older run
summaries that did not embed all metadata.

The generator rewrites screenshot paths to be relative to the dashboard HTML
file, so `file://` viewing works.

## Layout

- App view: choose the target app and jump into its replay space.
- Tier coverage: show scenario counts and visible-run pass totals.
- Sidebar: selected implementation runs, scenario list with per-run step
  progress, and failure inbox.
- Run summary: formal score remains the benchmark score, while stepwise score,
  contract failures, and probe counts explain cliffs without changing formal
  interpretation.
- Replay view: selected scenario shown step-by-step across all selected runs.
- Step blocks: action, component, pass/fail, screenshots, assertions, state
  diff, and final state.
- Failure rows: missing selectors, actionability errors, state probe errors,
  assertion failures, rejected/blocked mismatches, and scenario errors point to
  the first failed step with the recorded reason.
- Keyboard replay: left/right arrows move steps, up/down arrows move scenarios,
  and space toggles autoplay.

## Default Visibility

The default view selects the latest run for each subject. The intended mainline
subjects are:

- `reference`
- generated or manually collected candidate subjects
- known-bad subjects when explicitly included for diagnostic comparison

Diagnostic runs are still visible in the subject picker, but formal benchmark
interpretation should be based on scoring scenarios whose requirements are
derivable from the public DSL contract.
