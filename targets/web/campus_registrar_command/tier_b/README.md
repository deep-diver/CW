# Campus Registrar Command Tier B

Tier B reframes the campus registrar domain as a degree-clearance operations
center rather than a student course-planning tool. The public surface includes
an at-risk student queue, section matrix, time-conflict resolution, transfer
credit intake, bursar/advisor/registrar role gates, waitlist handling, release
ledger, audit trail, route persistence, and reload persistence.

The current implementation includes public scenarios and a reference static app.
Private scenarios have intentionally not been authored yet.

Run the public reference suite:

```bash
python -m detoxbench evaluate-dsl \
  --target targets/web/campus_registrar_command/tier_b \
  --static-dir targets/web/campus_registrar_command/tier_b/reference_app \
  --scenario-set public \
  --run-subject reference_app \
  --headless
```
