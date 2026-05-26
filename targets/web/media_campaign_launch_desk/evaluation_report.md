# Media Campaign Launch Desk Evaluation Report

Consolidated on 2026-05-15. This report covers the Tier A-D reference
validations and final Model Tier M/T/F blind repeat cohorts.

## Maintained Tiers

| Tier | Focus | Reference result |
| --- | --- | ---: |
| A | Creative asset selection with campaign metadata, channel scheduling, budget commit, rights check, legal approval, launch ledger, and persistence | 24/24 scenarios, 84/84 formal |
| B | Broadcast release switcher with source wall, rundown timing, caption/localization gates, partner traffic board, transmission ledger, and persistence | 12/12 public scenarios, 46/46 formal |
| C | Omnichannel media investment control room with audience maps, channel-mix allocation, reach/frequency forecast, inventory intake, experiments, pacing guardrails, activation ledger, and persistence | 44/44 scenarios, 175/175 formal |
| D | Global premiere embargo command center with release-code/watermark locks, blackout matrices, partner manifests, beacons, sentiment/escrow gates, multi-role sign-off, and post-seal reopening | 48/48 scenarios, 189/189 formal |

## Official Blind Batches

| Tier | Model tiers | Batch |
| --- | --- | --- |
| A | M, 10 repetitions per model | `20260514_media_tiera_m_10x` |
| A | T/F, 10 repetitions per model | `20260514_media_tiera_tf_10x` |
| B | M/T/F, 10 repetitions per model | `20260514_media_tierb_redesign_mtf_10x` |
| C | M/T/F, 10 repetitions per model | `20260515T_media_tierc_mtf_10x` |
| D | M/T/F, 10 repetitions per model | `20260515T_media_tierd_mtf_10x` |

Raw cohort artifacts are local and gitignored under `cohorts/`.

## Tier Rollup

| Tier | Runs | Scenario pass mean | Formal mean | Stepwise mean | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: |
| A / M | 30 | 4.20/24 | 17.3% | 32.7% | 0/30 |
| A / T | 30 | 11.83/24 | 49.2% | 54.8% | 11/30 |
| A / F | 30 | 23.07/24 | 95.8% | 98.0% | 26/30 |
| B / M | 30 | 0.83/12 | 7.2% | 21.3% | 0/30 |
| B / T | 30 | 5.13/12 | 42.5% | 50.0% | 10/30 |
| B / F | 30 | 10.43/12 | 86.7% | 91.5% | 18/30 |
| C / M | 30 | 13.93/44 | 31.4% | 41.3% | 2/30 |
| C / T | 30 | 18.10/44 | 41.0% | 54.0% | 2/30 |
| C / F | 30 | 34.20/44 | 77.3% | 81.9% | 16/30 |
| D / M | 30 | 6.37/48 | 12.2% | 25.1% | 0/30 |
| D / T | 30 | 10.97/48 | 22.2% | 30.2% | 0/30 |
| D / F | 29 | 30.10/48 | 61.5% | 69.9% | 1/29 |

## Tier A Model-Tier Detail

| Model | Runs | Scenario pass mean | Formal mean | Stepwise mean | Contract mean | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gpt-5.4-nano` | 10 | 6.20/24 | 26.8% | 38.6% | 72.1% | 0/10 |
| `claude-haiku-4-5` | 10 | 5.50/24 | 21.7% | 42.3% | 62.9% | 0/10 |
| `gemini-3.1-flash-lite` | 10 | 0.90/24 | 3.3% | 17.2% | 70.4% | 0/10 |
| `gpt-5.4-mini` | 10 | 2.20/24 | 9.8% | 16.2% | 70.0% | 0/10 |
| `claude-sonnet-4-6` | 10 | 16.60/24 | 67.9% | 75.2% | 90.0% | 5/10 |
| `gemini-flash-latest` | 10 | 16.70/24 | 69.9% | 73.1% | 100.0% | 6/10 |
| `gpt-5.4` | 10 | 23.80/24 | 99.8% | 100.0% | 100.0% | 9/10 |
| `claude-opus-4-6` | 10 | 24.00/24 | 100.0% | 100.0% | 100.0% | 10/10 |
| `gemini-3.1-pro-preview` | 10 | 21.40/24 | 87.5% | 94.0% | 92.9% | 7/10 |

## Tier B Model-Tier Detail

| Model | Runs | Scenario pass mean | Formal mean | Stepwise mean | Contract mean | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gpt-5.4-nano` | 10 | 1.90/12 | 17.2% | 34.1% | 60.0% | 0/10 |
| `claude-haiku-4-5` | 10 | 0.60/12 | 4.3% | 18.1% | 39.2% | 0/10 |
| `gemini-3.1-flash-lite` | 10 | 0.00/12 | 0.0% | 11.7% | 77.5% | 0/10 |
| `gpt-5.4-mini` | 10 | 0.00/12 | 0.0% | 7.9% | 80.0% | 0/10 |
| `claude-sonnet-4-6` | 10 | 10.80/12 | 89.8% | 92.1% | 93.3% | 8/10 |
| `gemini-flash-latest` | 10 | 4.60/12 | 37.6% | 50.1% | 87.5% | 2/10 |
| `gpt-5.4` | 10 | 10.20/12 | 85.0% | 93.8% | 93.3% | 2/10 |
| `claude-opus-4-6` | 10 | 11.90/12 | 99.1% | 99.9% | 100.0% | 9/10 |
| `gemini-3.1-pro-preview` | 10 | 9.20/12 | 75.9% | 80.7% | 90.0% | 7/10 |

## Tier C Model-Tier Detail

The retained Tier C report contains model-tier rollups for the final blind
cohort. The per-model raw cohort artifacts are gitignored and are not present
in this checkout, so per-model metrics are listed as unavailable rather than
being inferred from group averages.

| Group | Model | Runs | Scenario pass mean | Formal mean | Stepwise mean | Full pass | Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| M | **Group aggregate** | 30 | 13.93/44 | 31.4% | 41.3% | 2/30 | retained report |
| M | `gpt-5.4-nano` | -- | -- | -- | -- | -- | raw not retained |
| M | `claude-haiku-4-5` | -- | -- | -- | -- | -- | raw not retained |
| M | `gemini-3.1-flash-lite` | -- | -- | -- | -- | -- | raw not retained |
| T | **Group aggregate** | 30 | 18.10/44 | 41.0% | 54.0% | 2/30 | retained report |
| T | `gpt-5.4-mini` | -- | -- | -- | -- | -- | raw not retained |
| T | `claude-sonnet-4-6` | -- | -- | -- | -- | -- | raw not retained |
| T | `gemini-flash-latest` | -- | -- | -- | -- | -- | raw not retained |
| F | **Group aggregate** | 30 | 34.20/44 | 77.3% | 81.9% | 16/30 | retained report |
| F | `gpt-5.4` | -- | -- | -- | -- | -- | raw not retained |
| F | `claude-opus-4-6` | -- | -- | -- | -- | -- | raw not retained |
| F | `gemini-3.1-pro-preview` | -- | -- | -- | -- | -- | raw not retained |

## Tier D Model-Tier Detail

The retained Tier D report contains model-tier rollups for the final blind
cohort. One Gemini Pro generation hung during the final cohort and was excluded
from scoring, leaving 29 evaluated F-tier runs. The per-model raw cohort
artifacts are gitignored and are not present in this checkout, so per-model
metrics are listed as unavailable rather than being inferred from group
averages.

| Group | Model | Runs | Scenario pass mean | Formal mean | Stepwise mean | Full pass | Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| M | **Group aggregate** | 30 | 6.37/48 | 12.2% | 25.1% | 0/30 | retained report |
| M | `gpt-5.4-nano` | -- | -- | -- | -- | -- | raw not retained |
| M | `claude-haiku-4-5` | -- | -- | -- | -- | -- | raw not retained |
| M | `gemini-3.1-flash-lite` | -- | -- | -- | -- | -- | raw not retained |
| T | **Group aggregate** | 30 | 10.97/48 | 22.2% | 30.2% | 0/30 | retained report |
| T | `gpt-5.4-mini` | -- | -- | -- | -- | -- | raw not retained |
| T | `claude-sonnet-4-6` | -- | -- | -- | -- | -- | raw not retained |
| T | `gemini-flash-latest` | -- | -- | -- | -- | -- | raw not retained |
| F | **Group aggregate** | 29 | 30.10/48 | 61.5% | 69.9% | 1/29 | retained report |
| F | `gpt-5.4` | -- | -- | -- | -- | -- | raw not retained |
| F | `claude-opus-4-6` | -- | -- | -- | -- | -- | raw not retained |
| F | `gemini-3.1-pro-preview` | -- | -- | -- | -- | -- | raw not retained; one generation excluded |

## Difficulty Notes

Media Campaign Launch Desk Tier A is in a plausible Tier A band at Model Tier
M/T, but it becomes easy for Model Tier F. This is still acceptable for a Tier
A target because weak models do not solve it and Tier T remains mixed; however,
F-tier saturation is higher than Campus Registrar, especially for GPT-5.4 and
Claude Opus. First failures continue to cluster around asset filtering,
campaign metadata normalization, rights checks, and early launch scheduling.

The redesigned Media Campaign Launch Desk Tier B is accepted. It is visually
and mechanically distinct from Campus Registrar: it uses a broadcast release
switcher, source wall, rundown/runtime locks, caption/localization gates,
partner traffic, and transmission release instead of administrative clearance
tables. Difficulty moved in the intended direction versus Tier A: Model Tier M
is lower, Tier T remains mixed, and Model Tier F is no longer saturated.

Media Campaign Launch Desk Tier C is a substantial escalation from B in product
surface and workflow depth, but still allows many F-tier full solves. That makes
it a useful C target rather than a D target: M/T remain mixed, while F can often
reconstruct the omnichannel investment room.

Media Campaign Launch Desk Tier D is the final hard target. M/T have zero full
solves, and F has only one full solve across 29 evaluated runs. One Gemini Pro
generation hung during the final cohort and was excluded from scoring. The
difficulty comes from the combined embargo, market-window, partner manifest,
measurement, sentiment, escrow, sign-off, seal, and post-seal invalidation
logic.
