# Campus Registrar Command Repeat Cohort

Batch root: `/Users/chansungpark/Developers/backup/b/detoxbench/targets/web/campus_registrar_command/cohorts/_batches/rerun_missing_gemini_20260525T132231Z`

Evaluated: 40 / 40

## Tier x Model Group

| Target Tier | Model Tier | Runs | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd |
|---|---:|---:|---:|---:|---:|
| C | M | 10 | 0.000 ± 0.000 | 0.063 ± 0.033 | 0.993 ± 0.022 |
| C | T | 10 | 0.282 ± 0.365 | 0.397 ± 0.444 | 1.000 ± 0.000 |
| D | M | 10 | 0.000 ± 0.000 | 0.057 ± 0.000 | 0.700 ± 0.483 |
| D | T | 10 | 0.270 ± 0.289 | 0.421 ± 0.387 | 0.991 ± 0.028 |

## Model Detail

| Target | Group | Model | Runs | Scenario pass mean ± sd | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd | Top first failures |
|---|---:|---|---:|---:|---:|---:|---:|---|
| C | M | `gemini-3.1-flash-lite` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.063 ± 0.033 | 0.993 ± 0.022 | public_01_filter_queue_and_select_nova (10) |
| C | T | `gemini-flash-latest` | 10/10 | 8.70 ± 11.25 | 0.282 ± 0.365 | 0.397 ± 0.444 | 1.000 ± 0.000 | public_01_filter_queue_and_select_nova (6), public_07_bursar_clearance_after_exception_packet (4) |
| D | M | `gemini-3.1-flash-lite` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.057 ± 0.000 | 0.700 ± 0.483 | public_01_filter_wave_stack_and_select_iona (10) |
| D | T | `gemini-flash-latest` | 10/10 | 10.60 ± 11.30 | 0.270 ± 0.289 | 0.421 ± 0.387 | 0.991 ± 0.028 | public_01_filter_wave_stack_and_select_iona (6), public_07_identity_service_and_name_variance_resolution (3), public_03_policy_epoch_mismatch_then_lock (1) |
