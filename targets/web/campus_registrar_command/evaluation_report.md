# Campus Registrar Command Evaluation Report

Consolidated on 2026-05-15. This report covers the Tier A-D reference
validations and final Model Tier M/T/F blind repeat cohorts.

## Maintained Tiers

| Tier | Focus | Reference result |
| --- | --- | ---: |
| A | Student course planning with catalog filtering, schedule planning, eligibility check, enrollment ledger, waitlist, advisor override, and persistence | 24/24 scenarios, 84/84 formal |
| B | Registrar clearance command with at-risk queue, section matrix, time conflict resolution, petition gates, waitlist admission, release ledger, and persistence | 12/12 public scenarios, 44/44 formal |
| C | Graduation certification command with degree-audit heatmap, residency exception, aid clearance, dean vote, registrar certification, diploma release, and blocker ledger | 29/29 scenarios, 118/118 formal |
| D | Multi-authority graduation wave command with policy epoch lock, transcript/crosswalk imports, identity/bursar/diploma services, senate/provost gates, release wave, and accreditation freeze | 34/34 scenarios, 168/168 formal |

## Official Blind Batches

| Tier | Model tiers | Batch |
| --- | --- | --- |
| A | M, 10 repetitions per model | `20260514_campus_tiera_m_10x` |
| A | T/F, 10 repetitions per model | `20260514_campus_tiera_tf_10x` |
| B | M/T/F, 10 repetitions per model | `20260514_campus_tierb_mtf_10x` |
| C | M/T, 10 repetitions per model | `20260515T_campus_tierc_mt_10x` |
| C | F, 10 repetitions per model | `20260515T_f_hardening_v2_10x` |
| D | M/T, 10 repetitions per model | `20260515T_campus_tierd_mt_10x` |
| D | F, 10 repetitions per model | `20260515T_campus_tierd_f_10x` |

Raw cohort artifacts are local and gitignored under `cohorts/`.

## Tier Rollup

| Tier | Runs | Scenario pass mean | Formal mean | Stepwise mean | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: |
| A / M | 30 | 5.53/24 | 21.3% | 40.5% | 1/30 |
| A / T | 30 | 10.90/24 | 44.4% | 56.5% | 9/30 |
| A / F | 30 | 19.57/24 | 80.9% | 84.8% | 21/30 |
| B / M | 30 | 1.50/12 | 12.3% | 23.1% | 2/30 |
| B / T | 30 | 5.70/12 | 47.3% | 61.2% | 5/30 |
| B / F | 30 | 10.03/12 | 83.6% | 86.2% | 23/30 |
| C / M | 30 | 2.73/29 | 9.2% | 17.3% | 0/30 |
| C / T | 30 | 7.67/29 | 25.7% | 34.1% | 2/30 |
| C / F | 30 | 21.00/29 | 71.0% | 83.9% | 4/30 |
| D / M | 30 | 3.57/34 | 9.8% | 20.4% | 0/30 |
| D / T | 30 | 9.27/34 | 26.5% | 32.8% | 2/30 |
| D / F | 30 | 26.83/34 | 77.4% | 89.0% | 1/30 |

## Tier A Model-Tier Detail

| Model | Runs | Scenario pass mean | Formal mean | Stepwise mean | Contract mean | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gpt-5.4-nano` | 10 | 5.60/24 | 21.0% | 40.8% | 57.5% | 0/10 |
| `claude-haiku-4-5` | 10 | 9.50/24 | 37.5% | 57.9% | 43.8% | 1/10 |
| `gemini-3.1-flash-lite` | 10 | 1.50/24 | 5.5% | 22.8% | 77.9% | 0/10 |
| `gpt-5.4-mini` | 10 | 5.50/24 | 23.2% | 36.7% | 59.2% | 1/10 |
| `claude-sonnet-4-6` | 10 | 18.90/24 | 75.8% | 84.8% | 79.6% | 6/10 |
| `gemini-flash-latest` | 10 | 8.30/24 | 34.0% | 48.1% | 65.4% | 2/10 |
| `gpt-5.4` | 10 | 17.40/24 | 71.1% | 76.8% | 93.3% | 6/10 |
| `claude-opus-4-6` | 10 | 19.20/24 | 80.0% | 82.2% | 100.0% | 8/10 |
| `gemini-3.1-pro-preview` | 10 | 22.10/24 | 91.5% | 95.5% | 92.9% | 7/10 |

## Tier B Model-Tier Detail

| Model | Runs | Scenario pass mean | Formal mean | Stepwise mean | Contract mean | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gpt-5.4-nano` | 10 | 3.10/12 | 26.1% | 37.9% | 64.2% | 2/10 |
| `claude-haiku-4-5` | 10 | 1.40/12 | 10.9% | 25.1% | 55.0% | 0/10 |
| `gemini-3.1-flash-lite` | 10 | 0.00/12 | 0.0% | 6.2% | 70.0% | 0/10 |
| `gpt-5.4-mini` | 10 | 0.40/12 | 3.9% | 20.6% | 72.5% | 0/10 |
| `claude-sonnet-4-6` | 10 | 8.10/12 | 66.6% | 78.2% | 92.5% | 1/10 |
| `gemini-flash-latest` | 10 | 8.60/12 | 71.6% | 84.9% | 100.0% | 4/10 |
| `gpt-5.4` | 10 | 9.80/12 | 82.0% | 86.3% | 95.0% | 7/10 |
| `claude-opus-4-6` | 10 | 10.80/12 | 90.0% | 90.8% | 100.0% | 9/10 |
| `gemini-3.1-pro-preview` | 10 | 9.50/12 | 78.9% | 81.4% | 100.0% | 7/10 |

## Tier C Model-Tier Detail

M/T model-level rows were recovered from completed 2026-05-25 blind rerun
artifacts generated from the same public contracts and evaluated with the
same DSL browser evaluator. F rows remain from the retained tier README.

| Group | Model | Runs | Scenario pass mean | Formal mean | Stepwise mean | Contract mean | Full pass | Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| M | **Group aggregate** | 30 | 3.77/29 | 12.7% | 22.6% | 99.5% | 0/30 | recovered rerun |
| M | `gpt-5.4-nano` | 10 | 5.80/29 | 19.5% | 30.4% | 99.7% | 0/10 | recovered rerun |
| M | `claude-haiku-4-5` | 10 | 5.50/29 | 18.5% | 32.2% | 99.0% | 0/10 | recovered rerun |
| M | `gemini-3.1-flash-lite` | 10 | 0.00/29 | 0.0% | 5.3% | 100.0% | 0/10 | recovered rerun |
| T | **Group aggregate** | 30 | 12.23/29 | 41.8% | 47.2% | 100.0% | 8/30 | recovered rerun |
| T | `gpt-5.4-mini` | 10 | 0.00/29 | 0.0% | 3.2% | 100.0% | 0/10 | recovered rerun |
| T | `claude-sonnet-4-6` | 10 | 28.70/29 | 99.1% | 99.9% | 100.0% | 8/10 | recovered rerun |
| T | `gemini-flash-latest` | 10 | 8.00/29 | 26.2% | 38.7% | 100.0% | 0/10 | recovered rerun |
| F | **Group aggregate** | 30 | 21.00/29 | 71.0% | 83.9% | -- | 4/30 | retained report |
| F | `gpt-5.4` | 10 | 21.90/29 | 75.6% | 80.2% | -- | 2/10 | tier README |
| F | `claude-opus-4-6` | 10 | 22.40/29 | 73.4% | 89.5% | -- | 1/10 | tier README |
| F | `gemini-3.1-pro-preview` | 10 | 18.70/29 | 64.1% | 81.9% | -- | 1/10 | tier README |

## Tier D Model-Tier Detail

M/T model-level rows were recovered from completed 2026-05-25 blind rerun
artifacts generated from the same public contracts and evaluated with the
same DSL browser evaluator. F rows remain from the retained tier README.

| Group | Model | Runs | Scenario pass mean | Formal mean | Stepwise mean | Contract mean | Full pass | Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| M | **Group aggregate** | 30 | 4.23/34 | 11.9% | 20.2% | 100.0% | 0/30 | recovered rerun |
| M | `gpt-5.4-nano` | 10 | 5.40/34 | 14.9% | 23.3% | 100.0% | 0/10 | recovered rerun |
| M | `claude-haiku-4-5` | 10 | 7.30/34 | 20.9% | 31.4% | 100.0% | 0/10 | recovered rerun |
| M | `gemini-3.1-flash-lite` | 10 | 0.00/34 | 0.0% | 5.7% | 100.0% | 0/10 | recovered rerun |
| T | **Group aggregate** | 30 | 10.40/34 | 28.5% | 38.2% | 99.7% | 1/30 | recovered rerun |
| T | `gpt-5.4-mini` | 10 | 0.00/34 | 0.0% | 4.6% | 100.0% | 0/10 | recovered rerun |
| T | `claude-sonnet-4-6` | 10 | 20.50/34 | 58.2% | 67.8% | 100.0% | 1/10 | recovered rerun |
| T | `gemini-flash-latest` | 10 | 10.70/34 | 27.3% | 42.2% | 99.1% | 0/10 | recovered rerun |
| F | **Group aggregate** | 30 | 26.83/34 | 77.4% | 89.0% | -- | 1/30 | retained report |
| F | `gpt-5.4` | 10 | 24.80/34 | 70.5% | 82.7% | -- | 1/10 | tier README |
| F | `claude-opus-4-6` | 10 | 30.40/34 | 91.4% | 98.9% | -- | 0/10 | tier README |
| F | `gemini-3.1-pro-preview` | 10 | 25.30/34 | 70.2% | 85.6% | -- | 0/10 | tier README |

## Difficulty Notes

Campus Registrar Tier A lands in a plausible Tier A band across the model
ladder. Model Tier M remains weak and volatile, Tier T reaches partial-to-full
solves but still fails most runs, and Tier F solves the target often without
fully saturating it. The remaining failures still cluster around the first
catalog filter/actionability path and early plan/profile behavior, which is a
useful difficulty signal rather than pure tail-end scenario brittleness.

Campus Registrar Tier B is acceptable as a B-level target. Compared with Tier A,
Model Tier M is lower on formal and scenario progress, Model Tier T has fewer
full solves despite a similar formal mean, and Model Tier F remains high but not
fully saturated. The first-failure cluster stays near the at-risk queue and
early clearance selection path, which is a good signal that the added registrar
state machine is driving difficulty rather than only late persistence checks.

Campus Registrar Tier C is materially harder than B for M/T, while F can still
solve a small minority of runs. Its difficulty comes from the graduation
certification state graph: catalog locks, transfer equivalency import,
residency/aid/dean gates, registrar sealing, release persistence, and blocker
ledger recomputation.

Campus Registrar Tier D is the hardest maintained Campus tier. M remains very
low, T is volatile, and F reaches high partial scores but only one full solve in
30 runs. The remaining failures are concentrated around the multi-authority
release wave and accreditation-freeze interactions, which is the intended D
signal.
