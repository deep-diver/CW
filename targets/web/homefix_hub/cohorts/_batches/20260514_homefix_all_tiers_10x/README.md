# HomeFix Hub Repeat Cohort

Batch root: `/Users/chansungpark/Developers/backup/b/detoxbench/targets/web/homefix_hub/cohorts/_batches/20260514_homefix_all_tiers_10x`

Evaluated: 360 / 360

## Tier x Model Group

| Target Tier | Model Tier | Runs | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd |
|---|---:|---:|---:|---:|---:|
| A | F | 30 | 0.603 ± 0.268 | 0.793 ± 0.205 | 0.969 ± 0.167 |
| A | M | 30 | 0.271 ± 0.308 | 0.453 ± 0.341 | 0.726 ± 0.372 |
| A | T | 30 | 0.271 ± 0.366 | 0.408 ± 0.364 | 0.818 ± 0.339 |
| B | F | 30 | 0.675 ± 0.310 | 0.812 ± 0.266 | 0.917 ± 0.258 |
| B | M | 30 | 0.127 ± 0.260 | 0.262 ± 0.303 | 0.674 ± 0.422 |
| B | T | 30 | 0.307 ± 0.414 | 0.408 ± 0.406 | 0.891 ± 0.291 |
| C | F | 30 | 0.694 ± 0.277 | 0.848 ± 0.225 | 0.937 ± 0.241 |
| C | M | 30 | 0.048 ± 0.126 | 0.196 ± 0.209 | 0.572 ± 0.472 |
| C | T | 30 | 0.320 ± 0.413 | 0.424 ± 0.424 | 0.742 ± 0.405 |
| D | F | 30 | 0.656 ± 0.360 | 0.772 ± 0.321 | 0.969 ± 0.172 |
| D | M | 30 | 0.062 ± 0.151 | 0.219 ± 0.215 | 0.648 ± 0.427 |
| D | T | 30 | 0.227 ± 0.321 | 0.357 ± 0.366 | 0.849 ± 0.298 |

## Model Detail

| Target | Group | Model | Runs | Scenario pass mean ± sd | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd | Top first failures |
|---|---:|---|---:|---:|---:|---:|---:|---|
| A | F | `claude-opus-4-6` | 10/10 | 17.20 ± 4.80 | 0.647 ± 0.248 | 0.841 ± 0.110 | 1.000 ± 0.000 | public_03_booking_requires_slot (6), public_05_pro_accept_is_role_gated (1) |
| A | F | `gemini-3.1-pro-preview` | 10/10 | 16.80 ± 7.70 | 0.663 ± 0.331 | 0.792 ± 0.248 | 0.908 ± 0.290 | public_05_pro_accept_is_role_gated (3), public_01_filter_plumbing_services (1), public_02_quote_emergency_pipe_repair (1) |
| A | F | `gpt-5.4` | 10/10 | 14.10 ± 5.30 | 0.501 ± 0.206 | 0.745 ± 0.238 | 1.000 ± 0.000 | public_03_booking_requires_slot (4), public_04_book_visit_creates_timeline (3), public_01_filter_plumbing_services (2) |
| A | M | `claude-haiku-4-5` | 10/10 | 8.60 ± 8.07 | 0.341 ± 0.345 | 0.529 ± 0.348 | 0.667 ± 0.407 | public_01_filter_plumbing_services (4), public_02_quote_emergency_pipe_repair (2), public_04_book_visit_creates_timeline (2) |
| A | M | `gemini-3.1-flash-lite` | 10/10 | 1.00 ± 2.11 | 0.040 ± 0.083 | 0.178 ± 0.164 | 0.858 ± 0.299 | public_01_filter_plumbing_services (8), public_02_quote_emergency_pipe_repair (2) |
| A | M | `gpt-5.4-nano` | 10/10 | 11.40 ± 6.83 | 0.434 ± 0.294 | 0.654 ± 0.301 | 0.654 ± 0.403 | public_05_pro_accept_is_role_gated (4), public_01_filter_plumbing_services (3), public_02_quote_emergency_pipe_repair (2) |
| A | T | `claude-sonnet-4-6` | 10/10 | 11.00 ± 6.90 | 0.390 ± 0.277 | 0.618 ± 0.256 | 0.725 ± 0.367 | public_02_quote_emergency_pipe_repair (3), public_03_booking_requires_slot (3), public_01_filter_plumbing_services (2) |
| A | T | `gemini-flash-latest` | 10/10 | 10.20 ± 11.60 | 0.422 ± 0.483 | 0.517 ± 0.431 | 0.829 ± 0.343 | public_01_filter_plumbing_services (6), public_05_pro_accept_is_role_gated (1) |
| A | T | `gpt-5.4-mini` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.090 ± 0.032 | 0.900 ± 0.316 | public_01_filter_plumbing_services (10) |
| B | F | `claude-opus-4-6` | 10/10 | 22.50 ± 6.04 | 0.728 ± 0.243 | 0.855 ± 0.131 | 1.000 ± 0.000 | public_03_booking_requires_slot (4), public_05_pro_accept_is_role_gated (3) |
| B | F | `gemini-3.1-pro-preview` | 10/10 | 20.00 ± 9.65 | 0.685 ± 0.336 | 0.854 ± 0.247 | 0.852 ± 0.318 | public_15_dispatch_count_persists_after_reload (4), public_05_pro_accept_is_role_gated (2), public_01_filter_plumbing_services (1) |
| B | F | `gpt-5.4` | 10/10 | 18.70 ± 10.59 | 0.612 ± 0.360 | 0.728 ± 0.371 | 0.900 ± 0.316 | public_04_book_visit_creates_timeline (4), public_01_filter_plumbing_services (3), public_03_booking_requires_slot (2) |
| B | M | `claude-haiku-4-5` | 10/10 | 3.70 ± 6.04 | 0.104 ± 0.169 | 0.242 ± 0.263 | 0.555 ± 0.445 | public_01_filter_plumbing_services (7), public_02_quote_emergency_pipe_repair (2), public_04_book_visit_creates_timeline (1) |
| B | M | `gemini-3.1-flash-lite` | 10/10 | 2.70 ± 8.54 | 0.093 ± 0.294 | 0.184 ± 0.285 | 0.800 ± 0.422 | public_01_filter_plumbing_services (9), public_04_book_visit_creates_timeline (1) |
| B | M | `gpt-5.4-nano` | 10/10 | 5.70 ± 9.23 | 0.185 ± 0.313 | 0.360 ± 0.358 | 0.666 ± 0.405 | public_01_filter_plumbing_services (6), public_02_quote_emergency_pipe_repair (2), public_04_book_visit_creates_timeline (2) |
| B | T | `claude-sonnet-4-6` | 10/10 | 9.30 ± 12.40 | 0.301 ± 0.408 | 0.398 ± 0.420 | 0.900 ± 0.316 | public_01_filter_plumbing_services (6), public_05_pro_accept_is_role_gated (2), public_03_booking_requires_slot (1) |
| B | T | `gemini-flash-latest` | 10/10 | 18.60 ± 12.04 | 0.621 ± 0.412 | 0.732 ± 0.356 | 0.772 ± 0.380 | public_04_book_visit_creates_timeline (4), public_01_filter_plumbing_services (2), public_02_quote_emergency_pipe_repair (2) |
| B | T | `gpt-5.4-mini` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.094 ± 0.000 | 1.000 ± 0.000 | public_01_filter_plumbing_services (10) |
| C | F | `claude-opus-4-6` | 10/10 | 23.90 ± 4.12 | 0.729 ± 0.148 | 0.872 ± 0.103 | 1.000 ± 0.000 | public_05_pro_accept_is_role_gated (7), public_03_booking_requires_slot (2), public_13_permit_upload_persists_after_reload (1) |
| C | F | `gemini-3.1-pro-preview` | 10/10 | 19.40 ± 10.65 | 0.614 ± 0.349 | 0.826 ± 0.264 | 0.810 ± 0.401 | public_13_permit_upload_persists_after_reload (5), public_04_book_visit_creates_timeline (2), public_01_filter_plumbing_services (1) |
| C | F | `gpt-5.4` | 10/10 | 23.80 ± 9.38 | 0.740 ± 0.305 | 0.847 ± 0.287 | 1.000 ± 0.000 | public_04_book_visit_creates_timeline (4), public_13_permit_upload_persists_after_reload (2), private_13_invoice_total_persists_after_reload (1) |
| C | M | `claude-haiku-4-5` | 10/10 | 0.40 ± 0.70 | 0.012 ± 0.020 | 0.132 ± 0.126 | 0.513 ± 0.514 | public_01_filter_plumbing_services (9), public_02_quote_emergency_pipe_repair (1) |
| C | M | `gemini-3.1-flash-lite` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.079 ± 0.000 | 0.800 ± 0.422 | public_01_filter_plumbing_services (10) |
| C | M | `gpt-5.4-nano` | 10/10 | 4.50 ± 6.57 | 0.132 ± 0.198 | 0.376 ± 0.264 | 0.403 ± 0.426 | public_01_filter_plumbing_services (7), public_02_quote_emergency_pipe_repair (2), public_04_book_visit_creates_timeline (1) |
| C | T | `claude-sonnet-4-6` | 10/10 | 12.80 ± 14.24 | 0.398 ± 0.453 | 0.468 ± 0.463 | 0.748 ± 0.426 | public_01_filter_plumbing_services (5), public_13_permit_upload_persists_after_reload (2), public_02_quote_emergency_pipe_repair (1) |
| C | T | `gemini-flash-latest` | 10/10 | 18.30 ± 12.42 | 0.562 ± 0.397 | 0.741 ± 0.326 | 0.677 ± 0.401 | public_04_book_visit_creates_timeline (5), public_02_quote_emergency_pipe_repair (3), public_01_filter_plumbing_services (1) |
| C | T | `gpt-5.4-mini` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.063 ± 0.033 | 0.800 ± 0.422 | public_01_filter_plumbing_services (10) |
| D | F | `claude-opus-4-6` | 10/10 | 22.70 ± 10.64 | 0.620 ± 0.330 | 0.756 ± 0.283 | 1.000 ± 0.000 | public_03_booking_requires_slot (4), public_05_pro_accept_is_role_gated (2), private_14_materials_mismatch_persists_after_reload (1) |
| D | F | `gemini-3.1-pro-preview` | 10/10 | 25.80 ± 10.06 | 0.760 ± 0.316 | 0.888 ± 0.216 | 0.906 ± 0.298 | public_18_partial_warranty_table_marks_claim (6), public_02_quote_emergency_pipe_repair (1), public_03_booking_requires_slot (1) |
| D | F | `gpt-5.4` | 10/10 | 20.60 ± 14.97 | 0.589 ± 0.436 | 0.672 ± 0.422 | 1.000 ± 0.000 | public_01_filter_plumbing_services (4), public_04_book_visit_creates_timeline (3), private_14_materials_mismatch_persists_after_reload (1) |
| D | M | `claude-haiku-4-5` | 10/10 | 3.20 ± 4.61 | 0.077 ± 0.115 | 0.243 ± 0.202 | 0.371 ± 0.402 | public_01_filter_plumbing_services (7), public_02_quote_emergency_pipe_repair (3) |
| D | M | `gemini-3.1-flash-lite` | 10/10 | 0.10 ± 0.32 | 0.001 ± 0.002 | 0.092 ± 0.050 | 0.988 ± 0.037 | public_01_filter_plumbing_services (9), public_02_quote_emergency_pipe_repair (1) |
| D | M | `gpt-5.4-nano` | 10/10 | 3.80 ± 7.71 | 0.109 ± 0.232 | 0.322 ± 0.274 | 0.585 ± 0.454 | public_01_filter_plumbing_services (7), public_02_quote_emergency_pipe_repair (1), public_03_booking_requires_slot (1) |
| D | T | `claude-sonnet-4-6` | 10/10 | 14.10 ± 11.86 | 0.384 ± 0.348 | 0.511 ± 0.355 | 0.744 ± 0.270 | public_02_quote_emergency_pipe_repair (4), public_01_filter_plumbing_services (3), public_05_pro_accept_is_role_gated (1) |
| D | T | `gemini-flash-latest` | 10/10 | 10.80 ± 12.28 | 0.297 ± 0.347 | 0.490 ± 0.407 | 0.903 ± 0.307 | public_01_filter_plumbing_services (6), private_14_materials_mismatch_persists_after_reload (1), public_03_booking_requires_slot (1) |
| D | T | `gpt-5.4-mini` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.069 ± 0.024 | 0.900 ± 0.316 | public_01_filter_plumbing_services (10) |
