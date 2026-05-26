# Clinic Shift Command Evaluation Report

Consolidated on 2026-05-13. This report supersedes tier-specific evaluation notes for the maintained Clinic Shift Command target tiers.

## Maintained Tiers

Clinic Shift Command Tier A is not tracked on `main`; the final maintained target set begins at Tier B. Local ignored Tier A artifacts, if present in a developer workspace, are excluded from this report.

| Tier | Focus | Reference result |
| --- | --- | ---: |
| B | Multi-role clinic command center with capacity control, prior authorization, diagnostic release, referral upload, escalation closure, and handoff packet gates | 33/33 scenarios, 121/121 formal |
| C | Incident-command console with risk scoring, transport ETA, staffing exceptions, reconciliation/diversion matrices, readiness blockers, dual sign-off, audit trail, and final clearance | 52/52 scenarios, 195/195 formal |
| D | Final incident command seal with post-seal data invalidation, re-lock/re-seal, and diversion reopen gates | 55/55 scenarios, 207/207 formal |

## Official Blind Batches

| Tier | Batch |
| --- | --- |
| B | `20260513T022902Z_clinic_tierb_plus_mtf_10x` |
| C | `20260513T072758Z_clinic_tierc_readiness_mtf_10x` |
| D M/T | `tierd_mt_10x_20260513T2130Z` |
| D F | `tierd_f_10x_v3_20260513T2030Z` |

Raw cohort artifacts are local and gitignored under each tier's `cohorts/{M,T,F}/` directories.

## Tier Rollup

| Tier | Runs | Formal mean | Stepwise mean | Full pass |
| --- | ---: | ---: | ---: | ---: |
| B | 90 | 44.7% | 53.7% | 13/90 |
| C | 90 | 38.7% | 48.8% | 5/90 |
| D | 90 | 39.1% | 49.8% | 2/90 |

## Model-Tier Detail

| Target Tier | Model Tier | Runs | Formal mean | Stepwise mean | Full pass |
| --- | --- | ---: | ---: | ---: | ---: |
| B | M | 30 | 7.6% | 21.0% | 0/30 |
| B | T | 30 | 38.1% | 46.0% | 4/30 |
| B | F | 30 | 88.6% | 94.1% | 9/30 |
| C | M | 30 | 5.6% | 19.4% | 0/30 |
| C | T | 30 | 32.5% | 43.2% | 0/30 |
| C | F | 30 | 78.0% | 83.8% | 5/30 |
| D | M | 30 | 4.1% | 17.6% | 0/30 |
| D | T | 30 | 39.2% | 50.2% | 0/30 |
| D | F | 30 | 74.1% | 81.6% | 2/30 |

## Difficulty Notes

Clinic Shift Command has the highest partial progress among the three targets because stronger models can reproduce large parts of the operational command workflow. The full-pass curve still tightens across maintained tiers: Tier B has 13/90 complete solves, Tier C drops to 5/90, and Tier D drops to 2/90 after adding seal invalidation and reseal dependencies.
