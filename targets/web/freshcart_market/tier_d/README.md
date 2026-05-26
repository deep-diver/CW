# FreshCart Market Tier D

FreshCart Market Tier D turns the Tier C cold-chain grocery target into a
micro-fulfillment command product. It keeps the catalog, cart economics,
preparation, substitution, coupon, wallet, slot quote, restricted review,
fulfillment, and support flows, then adds a post-dispatch manifest seal that
requires the full review and cold-chain checklist to be complete.

## Scope

- DSL version: `3.0.0`
- Pages: 5
- Scenarios: 8 public, 26 private, 34 total
- Formal score: 119
- New Tier D surface: `dispatch_manifest_grid` plus `seal_dispatch_manifest_button`
- UI/UX brief: included in `app.ui_ux_brief` for consistent blind prompts

## Reference Validation

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/freshcart_market/tier_d \
  --static-dir targets/web/freshcart_market/tier_d/reference_app \
  --scenario-set all \
  --headless \
  --json
```

Current reference result: passed `34/34`, formal `119/119`, stepwise `119/119`.

Blind outputs are stored under `cohorts/{M,T,F}/<batch-id>/`.
