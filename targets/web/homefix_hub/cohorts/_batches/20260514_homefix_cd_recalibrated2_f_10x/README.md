# HomeFix Hub Repeat Cohort

Batch root: `/Users/chansungpark/Developers/backup/b/detoxbench/targets/web/homefix_hub/cohorts/_batches/20260514_homefix_cd_recalibrated2_f_10x`

Evaluated: 40 / 40

## Tier x Model Group

| Target Tier | Model Tier | Runs | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd |
|---|---:|---:|---:|---:|---:|
| C | F | 20 | 0.568 ± 0.357 | 0.685 ± 0.324 | 0.970 ± 0.132 |
| D | F | 20 | 0.390 ± 0.267 | 0.610 ± 0.310 | 0.953 ± 0.210 |

## Model Detail

| Target | Group | Model | Runs | Scenario pass mean ± sd | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd | Top first failures |
|---|---:|---|---:|---:|---:|---:|---:|---|
| C | F | `claude-opus-4-6` | 10/10 | 35.60 ± 16.17 | 0.696 ± 0.336 | 0.783 ± 0.295 | 1.000 ± 0.000 | public_05_pro_accept_is_role_gated (4), public_03_booking_requires_slot (2), public_01_filter_plumbing_services (1) |
| C | F | `gpt-5.4` | 10/10 | 23.40 ± 16.92 | 0.440 ± 0.345 | 0.586 ± 0.335 | 0.941 ± 0.187 | public_03_booking_requires_slot (4), public_04_book_visit_creates_timeline (3), public_01_filter_plumbing_services (2) |
| D | F | `claude-opus-4-6` | 10/10 | 29.50 ± 15.22 | 0.411 ± 0.236 | 0.586 ± 0.248 | 1.000 ± 0.000 | public_03_booking_requires_slot (6), public_01_filter_plumbing_services (2), public_04_book_visit_creates_timeline (1) |
| D | F | `gpt-5.4` | 10/10 | 25.90 ± 21.16 | 0.368 ± 0.307 | 0.633 ± 0.374 | 0.906 ± 0.296 | public_01_filter_plumbing_services (3), private_07_warranty_seal_full_journey (2), public_02_quote_emergency_pipe_repair (2) |
