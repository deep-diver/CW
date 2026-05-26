# FreshCart Market Tier A

FreshCart Market Tier A is a consumer grocery delivery benchmark target. It
covers catalog filtering, cart updates, coupon validation, checkout, order
history, role-gated cancellation, deterministic service fixtures, persistence,
and browser navigation.

Run the reference app:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/freshcart_market/tier_a \
  --static-dir targets/web/freshcart_market/tier_a/reference_app \
  --headless
```
