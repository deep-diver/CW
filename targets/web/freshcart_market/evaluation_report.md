# FreshCart Market Evaluation Report

Consolidated on 2026-05-13. This report supersedes tier-specific evaluation notes for the maintained FreshCart Market target tiers.

## Maintained Tiers

| Tier | Focus | Reference result |
| --- | --- | ---: |
| A | Consumer grocery marketplace with catalog filtering, cart, coupon, checkout, order history, cancellation, service fixtures, persistence, and navigation | 24/24 scenarios, 86/86 formal |
| B | Premium multi-vendor grocery operations with preparation options, loyalty services, delivery fees, fulfillment checklist, and staff confirmation | 29/29 scenarios, 111/111 formal |
| C | Advanced cold-chain operations with restricted review, wallet redemption, delivery slot quote, support tickets, and manager approvals | 31/31 scenarios, 107/107 formal |
| D | Micro-fulfillment command product with post-dispatch manifest seal after cold-chain, substitution, inventory, review, and support gates | 34/34 scenarios, 119/119 formal |

## Official Blind Batches

| Tier | Batch |
| --- | --- |
| A | `20260511T180907Z` |
| B M | `20260512T015752Z_redesign` |
| B T/F | `20260512T025450Z` |
| C | `20260512T152227Z_tierc_mtf_10x_genairc` |
| D M/T | `tierd_mt_10x_20260513T2130Z` |
| D F | `tierd_f_10x_20260513T1850Z` |

Raw cohort artifacts are local and gitignored under each tier's `cohorts/{M,T,F}/` directories.

## Tier Rollup

| Tier | Runs | Formal mean | Stepwise mean | Full pass |
| --- | ---: | ---: | ---: | ---: |
| A | 89 | 42.2% | 50.6% | 12/89 |
| B | 90 | 19.3% | 34.7% | 3/90 |
| C | 90 | 21.9% | 40.6% | 4/90 |
| D | 90 | 15.4% | 34.9% | 1/90 |

## Model-Tier Detail

| Target Tier | Model Tier | Runs | Formal mean | Stepwise mean | Full pass |
| --- | --- | ---: | ---: | ---: | ---: |
| A | M | 29 | 6.6% | 21.6% | 0/29 |
| A | T | 30 | 45.4% | 51.9% | 4/30 |
| A | F | 30 | 73.4% | 77.5% | 8/30 |
| B | M | 30 | 5.7% | 18.1% | 0/30 |
| B | T | 30 | 7.9% | 24.2% | 0/30 |
| B | F | 30 | 44.3% | 62.0% | 3/30 |
| C | M | 30 | 5.7% | 18.4% | 0/30 |
| C | T | 30 | 10.7% | 32.7% | 0/30 |
| C | F | 30 | 49.4% | 70.8% | 4/30 |
| D | M | 30 | 5.7% | 20.7% | 0/30 |
| D | T | 30 | 10.6% | 31.7% | 0/30 |
| D | F | 30 | 29.9% | 52.3% | 1/30 |

## Difficulty Notes

FreshCart Tier A remains comparatively solvable for stronger models. Tier B sharply lowers full-pass rate by moving from consumer shopping to operational fulfillment gates. Tier C and Tier D keep low full-pass rates while increasing domain specificity; Tier D is the strictest FreshCart tier by full-pass rate, with only 1 complete solve across 90 blind runs.
