# StayFlow Concierge Tier B

StayFlow Concierge Tier B is a separate target from Tier A. It does not
overwrite `targets/web/stayflow_concierge/tier_a`; it extends the same travel
concierge family with a larger state surface and longer cross-page journeys.

Tier B covers:

- ordered multi-city itinerary legs across Busan, Seoul, and Kyoto;
- per-leg add-ons that affect route-level totals;
- deterministic quote and promo services;
- primary guest validation plus CSV traveler manifest upload;
- route, quote, traveler, and role persistence across reload/history;
- agent-only checklist gates before confirmation;
- full journey scenarios that combine pricing, upload, validation, promo,
  hold, role switch, checklist, and final confirmation.

Blind implementations must receive the DSL contract only. They may receive
requirements for polished, domain-appropriate UI/UX, but they must not receive
the reference app, scenario files, evaluator logs, screenshots, or answer keys.

Model cohorts use the global M/T/F definitions in `docs/model-tiers.md`.

## Reference Status

| Subject | Scenarios | Formal | Stepwise | Contract |
| --- | ---: | ---: | ---: | ---: |
| `reference_all` | 29 / 29 | 100% | 100% | 100% |

Verification command:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/stayflow_concierge/tier_b \
  --static-dir targets/web/stayflow_concierge/tier_b/reference_app \
  --run-subject reference_all \
  --headless \
  --json
```

## Scenario Shape

| Tier | Scenarios |
| --- | ---: |
| smoke | 2 |
| core | 4 |
| validation | 3 |
| service | 7 |
| upload | 2 |
| permission | 3 |
| persistence | 5 |
| journey | 3 |

Tier B intentionally increases pressure on actionability and state coupling.
Compared with Tier A, it has more pages, more ordered collection state, more
service interactions, stronger upload-derived counters, and longer end-to-end
scenario chains.

## Blind Cohorts

| Model Tier | Subject | Model | Scenarios | Formal | Stepwise | Contract |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| M | `blind_gpt54_nano_01` | `gpt-5.4-nano` | 6 / 29 | 9.1% | 49.6% | 20.7% |
| M | `blind_claude_haiku45_01` | `claude-haiku-4-5` | 9 / 29 | 31.8% | 75.2% | 100% |
| M | `blind_gemini31_flash_lite_01` | `gemini-3.1-flash-lite` | 0 / 29 | 0.0% | 8.1% | 100% |
| T | `blind_gpt54_mini_01` | `gpt-5.4-mini` | 0 / 29 | 0.0% | 8.1% | 100% |
| T | `blind_claude_sonnet46_01` | `claude-sonnet-4-6` | 0 / 29 | 0.0% | 0.0% | 0% |
| T | `blind_gemini_flash_latest_t_01` | `gemini-flash-latest` | 19 / 29 | 67.3% | 94.7% | 100% |
| F | `blind_gpt54_01` | `gpt-5.4` | 20 / 29 | 70.9% | 95.5% | 100% |
| F | `blind_claude_opus46_01` | `claude-opus-4-6` | 21 / 29 | 66.4% | 94.9% | 100% |
| F | `blind_gemini31_pro_preview_01` | `gemini-3.1-pro-preview` | 0 / 29 | 0.0% | 8.1% | 100% |

Detailed Model Tier M record:

- `cohort-tier-b-model-tier-m.md`

Detailed Model Tier T record:

- `cohort-tier-b-model-tier-t.md`

Detailed Model Tier F record:

- `cohort-tier-b-model-tier-f.md`
