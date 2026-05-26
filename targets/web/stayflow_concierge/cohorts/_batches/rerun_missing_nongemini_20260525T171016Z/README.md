# StayFlow Repeat Cohort

Batch root: `/Users/chansungpark/Developers/backup/b/detoxbench/targets/web/stayflow_concierge/cohorts/_batches/rerun_missing_nongemini_20260525T171016Z`

Evaluated: 60 / 60

## Tier x Model Group

| Target Tier | Model Tier | Runs | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd |
|---|---:|---:|---:|---:|---:|
| D | F | 20 | 0.404 ± 0.258 | 0.634 ± 0.349 | 0.950 ± 0.224 |
| D | M | 20 | 0.089 ± 0.185 | 0.256 ± 0.290 | 0.596 ± 0.467 |
| D | T | 20 | 0.280 ± 0.369 | 0.387 ± 0.428 | 0.800 ± 0.410 |

## Model Detail

| Target | Group | Model | Runs | Scenario pass mean ± sd | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd | Top first failures |
|---|---:|---|---:|---:|---:|---:|---:|---|
| D | F | `claude-opus-4-6` | 10/10 | 12.70 ± 9.14 | 0.380 ± 0.277 | 0.598 ± 0.372 | 1.000 ± 0.000 | public_07_payment_shortfall_then_authorized (5), public_01_filter_jeju_inventory (3), public_03_quote_and_command_promo (2) |
| D | F | `gpt-5.4` | 10/10 | 14.40 ± 8.17 | 0.429 ± 0.249 | 0.670 ± 0.340 | 0.900 ± 0.316 | public_07_payment_shortfall_then_authorized (6), public_01_filter_jeju_inventory (2), public_03_quote_and_command_promo (2) |
| D | M | `claude-haiku-4-5` | 10/10 | 3.50 ± 6.04 | 0.095 ± 0.190 | 0.325 ± 0.323 | 0.693 ± 0.462 | public_01_filter_jeju_inventory (9), public_05_document_exception_resolution_requires_staff (1) |
| D | M | `gpt-5.4-nano` | 10/10 | 2.50 ± 5.68 | 0.083 ± 0.191 | 0.188 ± 0.251 | 0.500 ± 0.476 | public_01_filter_jeju_inventory (10) |
| D | T | `claude-sonnet-4-6` | 10/10 | 17.50 ± 9.81 | 0.560 ± 0.337 | 0.729 ± 0.355 | 1.000 ± 0.000 | public_07_payment_shortfall_then_authorized (6), public_01_filter_jeju_inventory (2) |
| D | T | `gpt-5.4-mini` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.045 ± 0.031 | 0.600 ± 0.516 | public_01_filter_jeju_inventory (10) |
