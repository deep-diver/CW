# Clinic Shift Command

Clinic Shift Command is a clinical operations benchmark target for ambulatory
care teams. It focuses on queue management, room assignment, insurance and prior
authorization, diagnostic release, referral packet intake, escalation closure,
shift handoff, incident command, readiness tracking, and final clearance.

Only the calibrated final Tier B, Tier C, and Tier D versions are maintained here. Local
blind cohort artifacts are gitignored under each tier's `cohorts/{M,T,F}/`
directory.

| Tier | Focus | Scenarios |
|---|---|---:|
| B | Multi-role capacity, prior auth, diagnostic release, referral upload, escalation closure, and handoff packet workflows | 33 |
| C | Incident command with risk scoring, transport ETA, staffing exceptions, reconciliation/diversion matrices, readiness blockers, dual sign-off, audit trail, and final clearance | 52 |
| D | Final incident command seal with post-seal data invalidation, re-lock/re-seal, and diversion reopen gates | 55 |

The consolidated cross-tier evaluation report is
[`evaluation_report.md`](evaluation_report.md).
