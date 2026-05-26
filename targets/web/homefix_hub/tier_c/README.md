# HomeFix Hub Tier C

HomeFix Hub C is an independent DetoxBench DSL 3.0 web target for a mass-market home repair service.

## Scope

- Focus: multi-trade renovation command, permit/photo upload, customer approval, dispatch, QA, and invoice
- Pages: 5
- Public scenarios: 17
- Private scenarios: 32
- Reference formal score target: 207
- UI/UX brief: included in `app.ui_ux_brief`

Run the reference app:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/homefix_hub/tier_c \
  --static-dir targets/web/homefix_hub/tier_c/reference_app \
  --scenario-set all \
  --headless
```
