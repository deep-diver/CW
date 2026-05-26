# Clinic Shift Command Tier D

Clinic Shift Command Tier D extends the incident-command Tier C target with a
final command seal. It keeps the patient queue, room assignment, insurance and
prior authorization, clinical assessment, risk scoring, diagnostics release,
transport, handoff, staffing, reconciliation, diversion, surge, dual sign-off,
final clearance, and audit trail flows, then adds a director-gated incident seal
ledger after final clearance.

## Scope

- DSL version: `3.0.0`
- Pages: 5
- Scenarios: 16 public, 39 private, 55 total
- Formal score: 207
- New Tier D surface: `incident_seal_grid` plus `seal_incident_command_button`
- UI/UX brief: included in `app.ui_ux_brief` for consistent blind prompts

## Reference Validation

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/clinic_shift_command/tier_d \
  --static-dir targets/web/clinic_shift_command/tier_d/reference_app \
  --scenario-set all \
  --headless \
  --json
```

Current reference result: passed `55/55`, formal `207/207`, stepwise `207/207`.

Blind outputs are stored under `cohorts/{M,T,F}/<batch-id>/`.
