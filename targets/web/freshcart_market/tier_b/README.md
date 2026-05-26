# FreshCart Market Tier B

FreshCart Market Tier B is the premium multi-vendor grocery operations target.
It covers vendor-grouped catalog behavior, cart preparation options, coupon and
loyalty services, delivery fees, checkout, order history, fulfillment checklist
state, and role-gated staff confirmation.

Run the reference app:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/freshcart_market/tier_b \
  --static-dir targets/web/freshcart_market/tier_b/reference_app \
  --headless
```
