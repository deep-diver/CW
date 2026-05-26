# HomeFix Hub Evaluation Report

Consolidated on 2026-05-14. This report covers the maintained HomeFix Hub
target tiers and the first complete blind difficulty cohort.

## Maintained Tiers

| Tier | Focus | Reference result |
| --- | --- | ---: |
| A | Consumer home repair booking concierge with service filtering, quote, visit booking, role-gated contractor acceptance, persistence, and visit ledger | 24/24 scenarios, 86/86 formal |
| B | Field dispatch operations product with crew scheduling, parts readiness, dispatch persistence, and customer handoff gates | 29/29 scenarios, 112/112 formal |
| C | Evidence QA and repair clearance product with permit/document upload, inspection queues, invoice readiness, post-QA rework, supplement invoice, and customer release gates | 49/49 scenarios, 207/207 formal |
| D | Claims conveyor and warranty command product with insurance preauthorization, materials reconciliation, risk gates, QA/invoice handoffs, warranty seal ledger, carrier hold, customer ack, reseal, and material reopen loops | 64/64 scenarios, 271/271 formal |

## Official Blind Batch

| Tiers | Model tiers | Batch |
| --- | --- | --- |
| A-D | M/T/F, 10 repetitions per model | `20260514_homefix_all_tiers_10x` |
| C-D recalibration | M/T/F, 10 repetitions per model | `20260514_homefix_cd_recalibrated2_f_10x` |

Raw cohort artifacts are local and gitignored under each tier's
`cohorts/{M,T,F}/` directories. The batch-level aggregate is also available
locally at `targets/web/homefix_hub/cohorts/_batches/20260514_homefix_all_tiers_10x/`.

## Original Full-Cohort Rollup

This table preserves the first A-D M/T/F batch for historical comparison. C and
D have since been recalibrated; use the recalibration tables below for the
current C/D difficulty signal.

| Tier | Runs | Scenario pass mean | Formal mean | Stepwise mean | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 90 | 10.03/24 | 38.2% | 55.1% | 11/90 |
| B | 90 | 11.24/29 | 37.0% | 49.4% | 6/90 |
| C | 90 | 11.46/31 | 35.4% | 48.9% | 1/90 |
| D | 90 | 11.23/34 | 31.5% | 44.9% | 3/90 |

## Original Model-Tier Detail

These model-tier rows also belong to the first full batch and are retained only
as the before-recalibration baseline for C/D.

| Target Tier | Model Tier | Runs | Scenario pass mean | Formal mean | Stepwise mean | Full pass |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| A | M | 30 | 7.00/24 | 27.1% | 45.3% | 0/30 |
| A | T | 30 | 7.07/24 | 27.1% | 40.8% | 4/30 |
| A | F | 30 | 16.03/24 | 60.3% | 79.3% | 7/30 |
| B | M | 30 | 4.03/29 | 12.7% | 26.2% | 0/30 |
| B | T | 30 | 9.30/29 | 30.7% | 40.8% | 2/30 |
| B | F | 30 | 20.40/29 | 67.5% | 81.2% | 4/30 |
| C | M | 30 | 1.63/31 | 4.8% | 19.6% | 0/30 |
| C | T | 30 | 10.37/31 | 32.0% | 42.4% | 1/30 |
| C | F | 30 | 22.37/31 | 69.4% | 84.8% | 0/30 |
| D | M | 30 | 2.37/34 | 6.2% | 21.9% | 0/30 |
| D | T | 30 | 8.30/34 | 22.7% | 35.7% | 1/30 |
| D | F | 30 | 23.03/34 | 65.6% | 77.2% | 2/30 |

## Recalibration Check

The first full HomeFix batch showed C/D were too easy for F-tier models:
C(F) formal was 69.4% and D(F) formal was 65.6%. The recalibrated C/D specs add
hidden post-QA rework, supplement/release, carrier hold, customer ack, reseal,
and material-reopen loops. Reference apps pass the expanded suites at 100%.

| Tier | Runs | Reference result | Scenario pass mean | Formal mean | Stepwise mean | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C | 90 | 49/49 scenarios, 207/207 formal | 19.18/49 | 37.8% | 48.7% | 2/90 |
| D | 90 | 64/64 scenarios, 271/271 formal | 15.62/64 | 22.3% | 40.9% | 0/90 |

| Target Tier | Model Tier | Runs | Formal mean | Stepwise mean | Full pass |
| --- | --- | ---: | ---: | ---: | ---: |
| C | M | 30 | 10.4% | 24.4% | 0/30 |
| C | T | 30 | 42.3% | 48.6% | 1/30 |
| C | F | 30 | 60.8% | 73.1% | 1/30 |
| D | M | 30 | 4.7% | 18.7% | 0/30 |
| D | T | 30 | 20.5% | 37.5% | 0/30 |
| D | F | 30 | 41.5% | 66.6% | 0/30 |

Full-pass difficulty is now aligned with the intended C/D relationship: C is
barely fully solved by T/F-tier models, while D has no full solve across M/T/F
in the latest calibration batch. Partial progress is still higher than
FreshCart D (29.9% F formal) and StayFlow D (39.9% F formal), so D should be
treated as full-pass-hard rather than zero-partial-progress-hard.
