# StayFlow Repeat Cohort

Batch root: `/Users/chansungpark/Developers/backup/b/detoxbench/targets/web/stayflow_concierge/cohorts/_batches/20260511_stayflow_ab_mtf_10x`

Evaluated: 20 / 20

## Tier x Model Group

| Target Tier | Model Tier | Runs | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd |
|---|---:|---:|---:|---:|---:|
| A | F | 20 | 0.778 ± 0.170 | 0.903 ± 0.081 | 0.880 ± 0.111 |

## Model Detail

| Target | Group | Model | Runs | Scenario pass mean ± sd | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd | Top first failures |
|---|---:|---|---:|---:|---:|---:|---:|---|
| A | F | `gemini-3.1-pro-preview` | 10/10 | 18.90 ± 3.45 | 0.796 ± 0.173 | 0.902 ± 0.084 | 0.870 ± 0.112 | private_03_addon_stack_recalculates_total (4), public_04_service_promo_credit (2), private_09_second_promo_call_keeps_service_count (1) |
| A | F | `gpt-5.4` | 10/10 | 17.90 ± 3.51 | 0.760 ± 0.175 | 0.904 ± 0.083 | 0.891 ± 0.115 | public_01_filter_seoul_catalog (4), public_04_service_promo_credit (3), private_03_addon_stack_recalculates_total (1) |
