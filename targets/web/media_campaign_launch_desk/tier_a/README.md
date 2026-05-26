# Media Campaign Launch Desk Tier A

Media Campaign Launch Desk Tier A is a DSL 3.0 web target for a brand campaign
launch product. It covers creative asset filtering, asset selection, campaign
metadata normalization, channel scheduling, deterministic rights checks, budget
commitment, legal-gated approval, launch creation, table rendering, route
navigation, and reload persistence.

The public contract includes `app.ui_ux_brief`; blind implementations should
receive that exact brief with the public contract so the visual product surface
is consistent across candidate runs.

Run the reference app:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/media_campaign_launch_desk/tier_a \
  --static-dir targets/web/media_campaign_launch_desk/tier_a/reference_app \
  --scenario-set all \
  --headless \
  --json
```
