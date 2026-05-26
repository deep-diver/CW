# Clinic Shift Command Tier B

Clinic Shift Command Tier B extends the Tier A ambulatory operations baseline
into a multi-role clinic command center. It adds charge-nurse capacity control,
billing prior authorization, clinician diagnostic ordering, referral document
upload, escalation closure, diagnostic release gating, finalized handoff
packets, and longer persistence journeys.

The public contract includes `app.ui_ux_brief`; blind implementations should
receive that exact brief with the public contract and public scenarios so UI/UX
expectations are consistent across models and runs. The Tier B brief explicitly
asks for a desktop screenshot that reads as harder than Tier A: queue pressure,
capacity map, authorization ledger, diagnostic board, referral intake, and
handoff/escalation surfaces should all feel coordinated in one product. The
current calibrated version adds a release gate that requires coverage and
prior-auth clearance before diagnostics can be released, plus a final handoff
packet that requires released diagnostics, uploaded referrals, and a closed
charge-nurse escalation.

Run the reference app evaluation:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/clinic_shift_command/tier_b \
  --static-dir targets/web/clinic_shift_command/tier_b/reference_app \
  --headless
```

Current reference result:

```text
passed: true
formal: 121/121 (100.0%)
stepwise: 121/121 (100.0%)
scenarios: 33/33
```

Desktop screenshots are stored in `screenshots/`.

Run the 10x M/T/F blind repeat cohort:

```bash
set -a; source "$HOME/.genai_rc"; set +a
python3 tools/run_clinic_tier_b_repeat_cohort.py \
  --repetitions 10 \
  --generation-workers 9 \
  --evaluation-workers 9
```

The latest recorded cohort summary is consolidated in
`targets/web/clinic_shift_command/evaluation_report.md`.
