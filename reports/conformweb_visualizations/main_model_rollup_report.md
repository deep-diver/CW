# Main Model Rollup Audit

- Complete group-level paper scope: 252/2160 (11.7%), S_scen=36.7%, S_step=49.4%
- Three previously missing reportable runs were filled from low-level summary.json evaluations: FreshCart A Claude Haiku r01, StayFlow C Gemini Pro r03, Media D Gemini Pro r01.
- No new Campus Registrar Frontier rerun is included; the aborted temporary batch was archived and excluded.
- Explicit per-model table coverage: complete 2,160 reportable runs. Some cells use retained per-model report/README rows rather than low-level raw summaries; no per-model value is inferred from a model-group aggregate.

## Group aggregates

- Mini: 6/720 (0.8%), S_scen=10.9%, S_step=24.8%
- Turbo: 72/720 (10.0%), S_scen=31.9%, S_step=43.9%
- Frontier: 174/720 (24.2%), S_scen=67.2%, S_step=79.3%

## Per-model rows

| model_group   | model                  |   planned_runs |   reportable_runs |   missing_or_excluded_runs |   full_pass_count |   full_pass_rate_reportable |   S_scen |   S_step |
|:--------------|:-----------------------|---------------:|------------------:|---------------------------:|------------------:|----------------------------:|---------:|---------:|
| Mini          | GPT-5.4 nano           |            240 |               240 |                          0 |                 5 |                      0.0208 |   0.1753 |   0.3200 |
| Mini          | Claude Haiku 4.5       |            240 |               240 |                          0 |                 1 |                      0.0042 |   0.1432 |   0.3152 |
| Mini          | Gemini 3.1 Flash Lite  |            240 |               240 |                          0 |                 0 |                      0.0000 |   0.0093 |   0.1092 |
| Turbo         | GPT-5.4 mini           |            240 |               240 |                          0 |                 3 |                      0.0125 |   0.0425 |   0.1349 |
| Turbo         | Claude Sonnet 4.6      |            240 |               240 |                          0 |                46 |                      0.1917 |   0.5498 |   0.6742 |
| Turbo         | Gemini 3.1 Flash       |            240 |               240 |                          0 |                23 |                      0.0958 |   0.3654 |   0.5085 |
| Frontier      | GPT-5.4                |            240 |               240 |                          0 |                47 |                      0.1958 |   0.6838 |   0.8104 |
| Frontier      | Claude Opus 4.6        |            240 |               240 |                          0 |                69 |                      0.2875 |   0.7084 |   0.8230 |
| Frontier      | Gemini 3.1 Pro Preview |            240 |               240 |                          0 |                58 |                      0.2417 |   0.6232 |   0.7466 |
