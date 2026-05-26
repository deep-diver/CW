# StayFlow Concierge Tier D

StayFlow Concierge Tier D extends the Tier C premium travel target into a
post-confirmation release war room. It keeps the existing multi-city itinerary,
traveler readiness, supplier hold, quote, promo, payment, approval, and final
confirmation flows, then adds a manager-gated Tier D release-seal ledger.

## Scope

- DSL version: `3.0.0`
- Pages: 6
- Scenarios: 11 public, 17 private, 28 total
- Formal score: 132
- New Tier D surface: `release_seal_grid` plus `seal_release_button`
- UI/UX brief: included in `app.ui_ux_brief` for consistent blind prompts

## Reference Validation

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/stayflow_concierge/tier_d \
  --static-dir targets/web/stayflow_concierge/tier_d/reference_app \
  --scenario-set all \
  --headless \
  --json
```

Current reference result: passed `28/28`, formal `132/132`, stepwise `132/132`.

Blind outputs are stored under `cohorts/{M,T,F}/<batch-id>/`.
