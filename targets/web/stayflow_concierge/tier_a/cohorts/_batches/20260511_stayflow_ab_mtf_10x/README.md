# StayFlow Repeat Cohort

Batch root: `/Users/chansungpark/Developers/detoxbench/artifacts/stayflow_repeat_cohorts/20260511_stayflow_ab_mtf_10x`

Evaluated: 180 / 180

## Tier x Model Group

| Target Tier | Model Tier | Runs | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd |
|---|---:|---:|---:|---:|---:|
| A | F | 30 | 0.729 ± 0.204 | 0.863 ± 0.161 | 0.870 ± 0.108 |
| A | M | 30 | 0.089 ± 0.165 | 0.266 ± 0.224 | 0.584 ± 0.392 |
| A | T | 30 | 0.231 ± 0.305 | 0.376 ± 0.326 | 0.688 ± 0.379 |
| B | F | 30 | 0.618 ± 0.335 | 0.780 ± 0.328 | 1.000 ± 0.000 |
| B | M | 30 | 0.151 ± 0.208 | 0.343 ± 0.313 | 0.487 ± 0.453 |
| B | T | 30 | 0.306 ± 0.375 | 0.462 ± 0.403 | 0.851 ± 0.345 |

## Model Detail

| Target | Group | Model | Runs | Scenario pass mean ± sd | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd | Top first failures |
|---|---:|---|---:|---:|---:|---:|---:|---|
| A | F | `claude-opus-4-6` | 10/10 | 15.20 ± 5.73 | 0.629 ± 0.236 | 0.783 ± 0.243 | 0.848 ± 0.105 | private_03_addon_stack_recalculates_total (5), public_01_filter_seoul_catalog (3), public_04_service_promo_credit (2) |
| A | F | `gemini-3.1-pro-preview` | 10/10 | 18.90 ± 3.45 | 0.796 ± 0.173 | 0.902 ± 0.084 | 0.870 ± 0.112 | private_03_addon_stack_recalculates_total (4), public_04_service_promo_credit (2), private_09_second_promo_call_keeps_service_count (1) |
| A | F | `gpt-5.4` | 10/10 | 17.90 ± 3.51 | 0.760 ± 0.175 | 0.904 ± 0.083 | 0.891 ± 0.115 | public_01_filter_seoul_catalog (4), public_04_service_promo_credit (3), private_03_addon_stack_recalculates_total (1) |
| A | M | `claude-haiku-4-5` | 10/10 | 2.10 ± 2.77 | 0.104 ± 0.137 | 0.259 ± 0.206 | 0.726 ± 0.356 | public_01_filter_seoul_catalog (10) |
| A | M | `gemini-3.1-flash-lite` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.177 ± 0.103 | 0.748 ± 0.352 | public_01_filter_seoul_catalog (10) |
| A | M | `gpt-5.4-nano` | 10/10 | 4.50 ± 5.36 | 0.163 ± 0.231 | 0.362 ± 0.299 | 0.278 ± 0.299 | public_01_filter_seoul_catalog (9), public_03_missing_guest_name_rejected (1) |
| A | T | `claude-sonnet-4-6` | 10/10 | 12.00 ± 7.54 | 0.506 ± 0.320 | 0.618 ± 0.349 | 0.539 ± 0.335 | public_01_filter_seoul_catalog (6), private_03_addon_stack_recalculates_total (3), public_03_missing_guest_name_rejected (1) |
| A | T | `gemini-flash-latest` | 10/10 | 4.20 ± 5.79 | 0.173 ± 0.234 | 0.372 ± 0.281 | 0.526 ± 0.435 | public_01_filter_seoul_catalog (7), public_02_select_busan_quote (1), public_03_missing_guest_name_rejected (1) |
| A | T | `gpt-5.4-mini` | 10/10 | 0.60 ± 1.90 | 0.012 ± 0.038 | 0.137 ± 0.120 | 1.000 ± 0.000 | public_01_filter_seoul_catalog (9), public_03_missing_guest_name_rejected (1) |
| B | F | `claude-opus-4-6` | 10/10 | 7.80 ± 8.23 | 0.226 ± 0.239 | 0.430 ± 0.367 | 1.000 ± 0.000 | public_01_filter_seoul_catalog (5), public_03_two_city_addons_and_quote (5) |
| B | F | `gemini-3.1-pro-preview` | 10/10 | 24.70 ± 5.36 | 0.815 ± 0.221 | 0.944 ± 0.094 | 1.000 ± 0.000 | private_13_reload_preserves_quote_and_itinerary (5), public_03_two_city_addons_and_quote (2), public_06_valid_trip_hold (2) |
| B | F | `gpt-5.4` | 10/10 | 24.60 ± 1.26 | 0.812 ± 0.020 | 0.964 ± 0.002 | 1.000 ± 0.000 | public_06_valid_trip_hold (9), public_01_filter_seoul_catalog (1) |
| B | M | `claude-haiku-4-5` | 10/10 | 8.30 ± 5.12 | 0.287 ± 0.181 | 0.588 ± 0.189 | 0.679 ± 0.386 | public_01_filter_seoul_catalog (10) |
| B | M | `gemini-3.1-flash-lite` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.073 ± 0.026 | 0.300 ± 0.483 | public_01_filter_seoul_catalog (10) |
| B | M | `gpt-5.4-nano` | 10/10 | 5.50 ± 7.04 | 0.165 ± 0.246 | 0.369 ± 0.363 | 0.483 ± 0.448 | public_01_filter_seoul_catalog (6), public_03_two_city_addons_and_quote (3), public_02_build_two_city_itinerary (1) |
| B | T | `claude-sonnet-4-6` | 10/10 | 19.00 ± 10.51 | 0.660 ± 0.364 | 0.808 ± 0.349 | 0.900 ± 0.316 | public_01_filter_seoul_catalog (7), private_13_reload_preserves_quote_and_itinerary (1), public_06_valid_trip_hold (1) |
| B | T | `gemini-flash-latest` | 10/10 | 5.60 ± 8.09 | 0.175 ± 0.276 | 0.380 ± 0.317 | 0.852 ± 0.316 | public_01_filter_seoul_catalog (8), public_03_two_city_addons_and_quote (1), public_04_manifest_upload_counts (1) |
| B | T | `gpt-5.4-mini` | 10/10 | 2.70 ± 5.81 | 0.084 ± 0.178 | 0.197 ± 0.290 | 0.800 ± 0.422 | public_01_filter_seoul_catalog (9), public_03_two_city_addons_and_quote (1) |
