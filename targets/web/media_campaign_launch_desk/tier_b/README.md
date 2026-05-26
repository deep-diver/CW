# Media Campaign Launch Desk Tier B

Tier B reframes the media campaign domain as a broadcast campaign release
switcher rather than a single campaign launch desk. The public surface includes
a studio source wall, large broadcast preview, rundown timeline, runtime
overrun trimming, caption/localization readiness, delivery package upload,
legal/finance role gates, outlet trafficking, transmission ledger, audit trail,
route persistence, and reload persistence.

The current implementation includes public scenarios and a reference static app.
Private scenarios have intentionally not been authored yet.

Run the public reference suite:

```bash
python -m detoxbench evaluate-dsl \
  --target targets/web/media_campaign_launch_desk/tier_b \
  --static-dir targets/web/media_campaign_launch_desk/tier_b/reference_app \
  --scenario-set public \
  --run-subject reference_app \
  --headless
```
