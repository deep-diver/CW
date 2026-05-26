# Campus Registrar Command Tier D

Tier D turns the registrar target into a multi-authority graduation wave command
floor. The target is intentionally much harder than Tier C through natural
product complexity: policy epoch locking, degree graph reconciliation, capstone
seat arbitration, transcript bundle intake, articulation crosswalks, identity
variance service, bursar bundle service, diploma-lane service, worksheet
reconciliation, committee vote quorum, senate docket, provost counterseal,
commencement wave sealing, diploma manifest publication, accreditation freeze
events, blocker ledger, service counters, browser history, and reload
persistence.

The current implementation includes 14 public scenarios, 20 private scenarios,
and a reference static app.

Run the full reference suite:

```bash
python -m detoxbench evaluate-dsl \
  --target targets/web/campus_registrar_command/tier_d \
  --static-dir targets/web/campus_registrar_command/tier_d/reference_app \
  --scenario-set all \
  --run-subject reference_app_tier_d \
  --headless
```

Reference validation on 2026-05-15:

| Scenarios | Formal | Stepwise | Contract | Run id |
| ---: | ---: | ---: | ---: | --- |
| 34 / 34 | 168 / 168 | 168 / 168 | 34 / 34 | `20260515-090422-32bb4c7b` |

Model Tier F 10-run blind cohort on 2026-05-15:

| Model | Runs | Scenario pass mean | Formal | Stepwise | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-6` | 10 | 30.40 / 34 | 91.4% | 98.9% | 0 / 10 |
| `gemini-3.1-pro-preview` | 10 | 25.30 / 34 | 70.2% | 85.6% | 0 / 10 |
| `gpt-5.4` | 10 | 24.80 / 34 | 70.5% | 82.7% | 1 / 10 |
| **Tier F** | **30** | **26.83 / 34** | **77.4%** | **89.0%** | **1 / 30** |

Screenshots:

- `screenshots/00_curriculum_dossier_desktop.png`
- `screenshots/01_release_freeze_desktop.png`
