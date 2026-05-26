# HomeFix Hub Tier B

HomeFix Hub B is an independent DetoxBench DSL 3.0 web target for a mass-market home repair service.

## Scope

- Focus: dispatcher quote approval, technician assignment, parts checklist, and role-gated dispatch
- Pages: 4
- Public scenarios: 16
- Private scenarios: 13
- Reference formal score target: 112
- UI/UX brief: included in `app.ui_ux_brief`

Run the reference app:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/homefix_hub/tier_b \
  --static-dir targets/web/homefix_hub/tier_b/reference_app \
  --scenario-set all \
  --headless
```
