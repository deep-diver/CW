# Campus Registrar Command Tier C

Tier C reframes the campus registrar domain as a graduation certification
command center. The public surface includes candidate risk radar, degree-audit
requirement heatmap, collision resolution, transfer articulation upload,
residency exception packet, aid/SAP clearance service, dean vote, registrar
certification, diploma release, blocker ledger, audit persistence, deterministic
bursar service calls, public dean/seal checksum derivation, and a final senate
hold system event.

The current implementation includes 12 public scenarios, 17 private scenarios,
and a reference static app. The scenario count is intentionally kept close to
the established 25-34 scenario range used by most mature web targets.

Run the full reference suite:

```bash
python -m detoxbench evaluate-dsl \
  --target targets/web/campus_registrar_command/tier_c \
  --static-dir targets/web/campus_registrar_command/tier_c/reference_app \
  --scenario-set all \
  --run-subject reference_app \
  --headless
```

Reference validation on 2026-05-14 passed all 29 scenarios with formal,
stepwise, and contract scores at 100%.

Final Model Tier F 10-run blind cohort:

| Model | Runs | Scenario pass mean | Formal | Stepwise | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-6` | 10 | 22.40 / 29 | 73.4% | 89.5% | 1 / 10 |
| `gpt-5.4` | 10 | 21.90 / 29 | 75.6% | 80.2% | 2 / 10 |
| `gemini-3.1-pro-preview` | 10 | 18.70 / 29 | 64.1% | 81.9% | 1 / 10 |
| **Tier F** | **30** | **21.00 / 29** | **71.0%** | **83.9%** | **4 / 30** |
