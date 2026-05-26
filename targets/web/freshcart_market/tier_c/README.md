# FreshCart Market Tier C

FreshCart Market Tier C is the advanced cold-chain grocery operations target. It builds on the Tier A/B catalog, cart, coupon, and fulfillment flows, then adds cold-chain packaging fees, restricted-item review, slot quote services, wallet redemption, support tickets, and manager-gated approvals.

Run the reference app evaluation:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/freshcart_market/tier_c \
  --static-dir targets/web/freshcart_market/tier_c/reference_app \
  --headless
```

Run the 10x blind M/T/F repeat cohort:

```bash
set -a
source "$HOME/.genai_rc"
set +a
python3 tools/run_freshcart_tierc_repeat_cohort.py \
  --batch-id "$(date -u +%Y%m%dT%H%M%SZ)_tierc_mtf_10x" \
  --repetitions 10 \
  --generation-workers 6 \
  --evaluation-workers 6 \
  --max-retries 2
```

See `../evaluation_report.md` for the consolidated cross-tier cohort result.
