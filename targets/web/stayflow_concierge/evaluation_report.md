# StayFlow Concierge Evaluation Report

Consolidated on 2026-05-13. This report supersedes tier-specific evaluation notes for the maintained StayFlow Concierge target tiers.

## Maintained Tiers

| Tier | Focus | Reference result |
| --- | --- | ---: |
| A | Single-city travel booking baseline with filtering, add-ons, promo validation, guest validation, manifest upload, agent confirmation, persistence, and history checks | 23/23 scenarios, 83/83 formal |
| B | Multi-city concierge with ordered itinerary legs, quote/promo services, traveler manifests, role-gated checklist, and final confirmation | 29/29 scenarios, 110/110 formal |
| C | Trip operations command center with quote, payment, supplier hold, conflict repair, approval, and checkout journey | 25/25 scenarios, 119/119 formal |
| D | Post-confirmation release war room with manager-gated release seal ledger | 28/28 scenarios, 132/132 formal |

## Official Blind Batches

| Tier | Batch |
| --- | --- |
| A | `20260511_stayflow_ab_mtf_10x` |
| B | `20260511_stayflow_ab_mtf_10x` |
| C | `stayflow-tier-c-20260511T153500Z` |
| D M/T | `tierd_mt_10x_20260513T2130Z` |
| D F | `tierd_f_10x_20260513T1850Z` |

Raw cohort artifacts are local and gitignored under each tier's `cohorts/{M,T,F}/` directories.

## Tier Rollup

| Tier | Runs | Formal mean | Stepwise mean | Full pass |
| --- | ---: | ---: | ---: | ---: |
| A | 90 | 34.9% | 50.2% | 2/90 |
| B | 90 | 35.8% | 52.8% | 2/90 |
| C | 89 | 20.1% | 39.8% | 1/89 |
| D | 90 | 23.3% | 41.3% | 1/90 |

## Model-Tier Detail

| Target Tier | Model Tier | Runs | Formal mean | Stepwise mean | Full pass |
| --- | --- | ---: | ---: | ---: | ---: |
| A | M | 30 | 8.9% | 26.6% | 0/30 |
| A | T | 30 | 23.1% | 37.6% | 0/30 |
| A | F | 30 | 72.9% | 86.3% | 2/30 |
| B | M | 30 | 15.1% | 34.3% | 0/30 |
| B | T | 30 | 30.6% | 46.2% | 1/30 |
| B | F | 30 | 61.8% | 78.0% | 1/30 |
| C | M | 30 | 2.7% | 13.5% | 0/30 |
| C | T | 30 | 19.8% | 40.2% | 1/30 |
| C | F | 29 | 38.4% | 66.6% | 0/29 |
| D | M | 30 | 6.9% | 19.0% | 0/30 |
| D | T | 30 | 23.1% | 41.8% | 0/30 |
| D | F | 30 | 39.9% | 63.1% | 1/30 |

## Difficulty Notes

StayFlow's full-pass rate stays low across all maintained tiers. Tier C and Tier D reduce full solves relative to the easier consumer booking surfaces by adding more cross-page state, supplier/payment dependencies, role gates, and post-confirmation ledger synchronization. Tier D is the current hardest StayFlow tier by full-pass rate among complete 90-run cohorts.
