# Media Campaign Launch Desk Tier C

Tier C reframes the media campaign domain as an omnichannel media investment
control room. The surface includes audience opportunity maps, channel-mix
allocation lanes, reach/frequency forecast cards, inventory-deal intake,
brand-safety validation, finance budget lock, holdout experiment cells,
measurement beacons, pacing guardrails, activation ledger, and audit
persistence.

The current implementation includes 24 public scenarios, 20 private scenarios,
and a reference static app.

Run the full reference suite:

```bash
python -m detoxbench evaluate-dsl \
  --target targets/web/media_campaign_launch_desk/tier_c \
  --static-dir targets/web/media_campaign_launch_desk/tier_c/reference_app \
  --scenario-set all \
  --run-subject reference_app \
  --headless
```
