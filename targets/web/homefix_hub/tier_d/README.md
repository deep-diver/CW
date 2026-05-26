# HomeFix Hub Tier D

HomeFix Hub D is an independent DetoxBench DSL 3.0 web target for a mass-market home repair service.

## Scope

- Focus: storm-response repair command with insurance preauth, materials reconciliation, QA, warranty seal, and post-seal invalidation
- Pages: 6
- Public scenarios: 18
- Private scenarios: 46
- Reference formal score target: 271
- UI/UX brief: included in `app.ui_ux_brief`

Run the reference app:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/homefix_hub/tier_d \
  --static-dir targets/web/homefix_hub/tier_d/reference_app \
  --scenario-set all \
  --headless
```
