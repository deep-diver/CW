# Campus Registrar Command Tier A

Campus Registrar Command Tier A is a DSL 3.0 web target for a university
registration product. It covers course filtering, course selection, student
profile normalization, eligibility checks, enrollment, waitlist creation,
advisor-gated override, table rendering, reload persistence, and basic route
navigation.

The public contract includes `app.ui_ux_brief`; blind implementations should
receive that exact brief with the public contract so the visual product surface
is consistent across candidate runs.

Run the reference app:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/campus_registrar_command/tier_a \
  --static-dir targets/web/campus_registrar_command/tier_a/reference_app \
  --scenario-set all \
  --headless \
  --json
```
