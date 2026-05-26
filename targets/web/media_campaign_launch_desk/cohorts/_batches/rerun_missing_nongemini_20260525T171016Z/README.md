# Media Campaign Launch Desk Repeat Cohort

Batch root: `/Users/chansungpark/Developers/backup/b/detoxbench/targets/web/media_campaign_launch_desk/cohorts/_batches/rerun_missing_nongemini_20260525T171016Z`

Evaluated: 120 / 120

## Tier x Model Group

| Target Tier | Model Tier | Runs | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd |
|---|---:|---:|---:|---:|---:|
| C | F | 20 | 0.898 ± 0.218 | 0.950 ± 0.206 | 1.000 ± 0.000 |
| C | M | 20 | 0.409 ± 0.449 | 0.544 ± 0.394 | 0.656 ± 0.438 |
| C | T | 20 | 0.337 ± 0.431 | 0.430 ± 0.439 | 0.776 ± 0.405 |
| D | F | 20 | 0.621 ± 0.420 | 0.713 ± 0.432 | 0.944 ± 0.224 |
| D | M | 20 | 0.185 ± 0.257 | 0.353 ± 0.373 | 0.736 ± 0.431 |
| D | T | 20 | 0.272 ± 0.404 | 0.358 ± 0.423 | 0.832 ± 0.367 |

## Model Detail

| Target | Group | Model | Runs | Scenario pass mean ± sd | Formal mean ± sd | Stepwise mean ± sd | Contract mean ± sd | Top first failures |
|---|---:|---|---:|---:|---:|---:|---:|---|
| C | F | `claude-opus-4-6` | 10/10 | 39.20 ± 13.83 | 0.890 ± 0.314 | 0.907 ± 0.292 | 1.000 ± 0.000 | public_01_filter_high_intent_audience_portfolio (1), public_05_finance_locks_forecast_budget (1) |
| C | F | `gpt-5.4` | 10/10 | 40.00 ± 1.63 | 0.906 ± 0.038 | 0.993 ± 0.005 | 1.000 ± 0.000 | public_05_finance_locks_forecast_budget (8), public_01_filter_high_intent_audience_portfolio (1) |
| C | M | `claude-haiku-4-5` | 10/10 | 9.90 ± 14.10 | 0.234 ± 0.325 | 0.422 ± 0.332 | 0.509 ± 0.434 | public_01_filter_high_intent_audience_portfolio (10) |
| C | M | `gpt-5.4-nano` | 10/10 | 25.90 ± 21.90 | 0.585 ± 0.501 | 0.666 ± 0.429 | 0.802 ± 0.411 | public_01_filter_high_intent_audience_portfolio (3), public_19_reset_clears_media_planning_state (2), public_02_select_urban_and_create_default_media_mix (1) |
| C | T | `claude-sonnet-4-6` | 10/10 | 29.20 ± 16.28 | 0.675 ± 0.373 | 0.783 ± 0.355 | 0.814 ± 0.394 | public_01_filter_high_intent_audience_portfolio (7), public_02_select_urban_and_create_default_media_mix (2), public_06_inventory_deal_upload_populates_deal_room (1) |
| C | T | `gpt-5.4-mini` | 10/10 | 0.00 ± 0.00 | 0.000 ± 0.000 | 0.078 ± 0.068 | 0.739 ± 0.434 | public_01_filter_high_intent_audience_portfolio (10) |
| D | F | `claude-opus-4-6` | 10/10 | 26.80 ± 23.07 | 0.544 ± 0.468 | 0.631 ± 0.471 | 1.000 ± 0.000 | private_20_post_seal_window_reupload_reopens_launch (6), public_01_filter_embargo_risk_assets (4) |
| D | F | `gpt-5.4` | 10/10 | 34.30 ± 18.21 | 0.699 ± 0.373 | 0.794 ± 0.398 | 0.887 ± 0.314 | private_20_post_seal_window_reupload_reopens_launch (5), public_01_filter_embargo_risk_assets (2), public_11_beacon_arm_and_attribution_health (1) |
| D | M | `claude-haiku-4-5` | 10/10 | 9.10 ± 14.06 | 0.166 ± 0.261 | 0.327 ± 0.312 | 0.773 ± 0.395 | public_01_filter_embargo_risk_assets (7), public_02_select_premiere_asset_snapshot (1), public_03_legal_service_clears_selected_asset (1) |
| D | M | `gpt-5.4-nano` | 10/10 | 11.40 ± 14.86 | 0.204 ± 0.265 | 0.380 ± 0.442 | 0.700 ± 0.483 | public_01_filter_embargo_risk_assets (7), public_05_release_code_watermark_and_asset_lock (2), public_03_legal_service_clears_selected_asset (1) |
| D | T | `claude-sonnet-4-6` | 10/10 | 25.30 ± 21.87 | 0.519 ± 0.451 | 0.611 ± 0.458 | 1.000 ± 0.000 | public_01_filter_embargo_risk_assets (4), public_05_release_code_watermark_and_asset_lock (3), private_13_sentiment_reupload_reopens_measurement_gate (2) |
| D | T | `gpt-5.4-mini` | 10/10 | 1.20 ± 3.79 | 0.025 ± 0.079 | 0.104 ± 0.156 | 0.665 ± 0.471 | public_01_filter_embargo_risk_assets (10) |
