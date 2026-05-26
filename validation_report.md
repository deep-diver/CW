# ConformWeb 2160-Run Validation Report

## Status

- Complete paper-scope group aggregate: PASS
- Complete model-level table coverage: PASS
- Missing/excluded runs after fill: 0

## Overall

- Total reportable runs: 2,160
- Full-pass count: 252
- Full-pass rate: 11.7%
- S_scen: 36.7%
- S_step: 49.4%

## Family Counts

- Travel: 9/360 (2.5%), S_scen=28.3%, S_step=45.0%
- Grocery: 20/360 (5.6%), S_scen=25.4%, S_step=40.6%
- Clinical Command: 44/360 (12.2%), S_scen=42.4%, S_step=52.5%
- Campus Registrar: 75/360 (20.8%), S_scen=44.5%, S_step=54.5%
- Media Campaign: 85/360 (23.6%), S_scen=45.7%, S_step=55.1%
- Home Services: 19/360 (5.3%), S_scen=33.8%, S_step=48.5%

## Model Groups

- Mini: 6/720 (0.8%), S_scen=10.9%, S_step=24.8%
- Turbo: 72/720 (10.0%), S_scen=31.9%, S_step=43.9%
- Frontier: 174/720 (24.2%), S_scen=67.2%, S_step=79.3%

## Tiers

- Tier A: 116/540 (21.5%)
- Tier B: 82/540 (15.2%)
- Tier C: 44/540 (8.1%)
- Tier D: 10/540 (1.9%)

## Per-Model Rollup

| model_group   | model                  |   reportable_runs |   full_pass_count |   full_pass_rate_reportable |   S_scen |   S_step |
|:--------------|:-----------------------|------------------:|------------------:|----------------------------:|---------:|---------:|
| Mini          | GPT-5.4 nano           |               240 |                 5 |                      0.0208 |   0.1753 |   0.3200 |
| Mini          | Claude Haiku 4.5       |               240 |                 1 |                      0.0042 |   0.1432 |   0.3152 |
| Mini          | Gemini 3.1 Flash Lite  |               240 |                 0 |                      0.0000 |   0.0093 |   0.1092 |
| Turbo         | GPT-5.4 mini           |               240 |                 3 |                      0.0125 |   0.0425 |   0.1349 |
| Turbo         | Claude Sonnet 4.6      |               240 |                46 |                      0.1917 |   0.5498 |   0.6742 |
| Turbo         | Gemini 3.1 Flash       |               240 |                23 |                      0.0958 |   0.3654 |   0.5085 |
| Frontier      | GPT-5.4                |               240 |                47 |                      0.1958 |   0.6838 |   0.8104 |
| Frontier      | Claude Opus 4.6        |               240 |                69 |                      0.2875 |   0.7084 |   0.8230 |
| Frontier      | Gemini 3.1 Pro Preview |               240 |                58 |                      0.2417 |   0.6232 |   0.7466 |

## Notes

- The three prior missing evaluations now have low-level `summary.json` results and are included.
- The aborted Campus Frontier rerun batch is archived under `reports/conformweb_visualizations/archives/aborted_reruns_20260526T0930/` and is excluded.
- Some retained per-model rows come from evaluation reports/tier README rollups rather than raw summaries; no model-level value is inferred from group aggregates.
