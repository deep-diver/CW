# Clinic Shift Command Tier C

Clinic Shift Command Tier C extends the calibrated Tier B clinic operations
target into an incident-command console for a high-acuity ambulatory clinic. It
adds deterministic patient risk scoring, transport ETA coordination, capacity
forecasting, staffing exception upload, wristband/transport reconciliation,
receiving-site diversion resolution, computed readiness/blocker tracking,
dual-role sign-off, final command clearance, and an audit trail that spans the
full multi-role journey.

The public contract includes `app.ui_ux_brief`; blind implementations should
receive that exact brief with the public contract and public scenarios so UI/UX
expectations are consistent across models and runs. The Tier C brief asks for a
polished desktop incident-command product with visible risk radar, floor-map,
forecast bands, staffing lane, transport ETA, reconciliation/diversion matrices,
readiness gauge, blocker ledger, command timeline, and audit log.

Run the reference app evaluation:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/clinic_shift_command/tier_c \
  --static-dir targets/web/clinic_shift_command/tier_c/reference_app \
  --headless
```

Current reference result:

```text
passed: true
formal: 195/195 (100.0%)
stepwise: 195/195 (100.0%)
scenarios: 52/52
```

Desktop screenshots are stored in `screenshots/`:

```text
targets/web/clinic_shift_command/tier_c/screenshots/01_command_board_desktop.png
targets/web/clinic_shift_command/tier_c/screenshots/02_chart_incident_workup_desktop.png
targets/web/clinic_shift_command/tier_c/screenshots/03_surge_command_clearance_desktop.png
```

Run the 10x M/T/F blind repeat cohort with the same prompt discipline used for
the calibrated Clinic Shift cohorts:

```bash
set -a; source "$HOME/.genai_rc"; set +a
python3 tools/run_clinic_tier_c_repeat_cohort.py \
  --repetitions 10 \
  --generation-workers 9 \
  --evaluation-workers 9
```

The latest recorded cohort summary is consolidated in
`targets/web/clinic_shift_command/evaluation_report.md`.
