# StayFlow Repeat Cohort

Batch root: `/Users/chansungpark/Developers/detoxbench/artifacts/stayflow_repeat_cohorts/stayflow-tier-c-20260511T153500Z`

Evaluated: 89 / 90

## Tier x Model Group

| Target Tier | Model Tier | Runs | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd |
|---|---:|---:|---:|---:|---:|
| C | F | 29 | 0.384 ± 0.258 | 0.666 ± 0.297 | 0.828 ± 0.218 |
| C | M | 30 | 0.027 ± 0.107 | 0.135 ± 0.197 | 0.601 ± 0.487 |
| C | T | 30 | 0.198 ± 0.261 | 0.402 ± 0.359 | 0.728 ± 0.401 |

## Model Detail

| Target | Group | Model | Runs | Scenario pass mean ± sd | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd | Top first failures |
|---|---:|---|---:|---:|---:|---:|---:|---|
| C | F | `claude-opus-4-6` | 10/10 | 11.20 ± 7.30 | 0.418 ± 0.298 | 0.675 ± 0.332 | 0.960 ± 0.042 | public_01_filter_jeju_inventory (8), public_03_quote_and_command_promo (2) |
| C | F | `gemini-3.1-pro-preview` | 9/10 | 9.11 ± 6.94 | 0.336 ± 0.271 | 0.629 ± 0.295 | 0.840 ± 0.166 | public_01_filter_jeju_inventory (6), public_03_quote_and_command_promo (2), public_07_payment_shortfall_then_authorized (1) |
| C | F | `gpt-5.4` | 10/10 | 10.50 ± 6.04 | 0.393 ± 0.223 | 0.689 ± 0.289 | 0.684 ± 0.282 | public_01_filter_jeju_inventory (9), public_07_payment_shortfall_then_authorized (1) |
| C | M | `claude-haiku-4-5` | 10/10 | 2.20 ± 4.73 | 0.082 ± 0.178 | 0.283 ± 0.287 | 0.696 ± 0.457 | public_01_filter_jeju_inventory (10) |
| C | M | `gemini-3.1-flash-lite` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.063 ± 0.000 | 0.600 ± 0.516 | public_01_filter_jeju_inventory (10) |
| C | M | `gpt-5.4-nano` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.059 ± 0.081 | 0.508 ± 0.519 | public_01_filter_jeju_inventory (10) |
| C | T | `claude-sonnet-4-6` | 10/10 | 10.10 ± 9.19 | 0.374 ± 0.351 | 0.548 ± 0.421 | 0.712 ± 0.395 | public_01_filter_jeju_inventory (6), public_03_quote_and_command_promo (2), public_02_four_city_route_pricing (1) |
| C | T | `gemini-flash-latest` | 10/10 | 6.00 ± 4.47 | 0.205 ± 0.151 | 0.536 ± 0.297 | 0.944 ± 0.100 | public_01_filter_jeju_inventory (7), public_03_quote_and_command_promo (3) |
| C | T | `gpt-5.4-mini` | 10/10 | 0.40 ± 1.26 | 0.015 ± 0.048 | 0.122 ± 0.137 | 0.528 ± 0.504 | public_01_filter_jeju_inventory (10) |
