# HomeFix Hub Tier A

HomeFix Hub A is an independent DetoxBench DSL 3.0 web target for a mass-market home repair service.

## Scope

- Focus: consumer home-repair booking, quote, visit scheduling, and pro acceptance
- Pages: 3
- Public scenarios: 14
- Private scenarios: 10
- Reference formal score target: 86
- UI/UX brief: included in `app.ui_ux_brief`

Run the reference app:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/homefix_hub/tier_a \
  --static-dir targets/web/homefix_hub/tier_a/reference_app \
  --scenario-set all \
  --headless
```
