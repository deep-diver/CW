# Media Campaign Launch Desk Tier D

Tier D is an independent global premiere embargo command target. It does not
reuse the Tier C media-mix control room. The product surface covers cinematic
release asset selection, legal clearance, normalized release/watermark locks,
market blackout uploads, partner traffic manifests, measurement beacons,
attribution health, sentiment risk, finance escrow, multi-role sign-offs,
readiness blocker recomputation, launch sealing, and post-seal reopening when
critical CSV inputs change.

The current implementation includes 20 public scenarios, 28 private scenarios,
and a reference static app.

Run the full reference suite:

```bash
python -m detoxbench evaluate-dsl \
  --target targets/web/media_campaign_launch_desk/tier_d \
  --static-dir targets/web/media_campaign_launch_desk/tier_d/reference_app \
  --scenario-set all \
  --run-subject reference_app \
  --headless
```
