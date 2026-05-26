# StayFlow Concierge Tier C

StayFlow Concierge Tier C is an independent DSL 3.0 target for a high-complexity travel concierge operations product. It does not replace or overwrite Tier A or Tier B; it is maintained as a separate target directory with its own contract, public/private scenarios, reference implementation, and local cohort artifacts.

## Scope

- Domain: premium multi-city travel booking and concierge support.
- App surface: consumer discovery, curated stay selection, guest/document readiness, concierge partner holds, protected checkout, and reservation confirmation.
- DSL version: `3.0.0`.
- Scenario split: 10 public scenarios and 15 private scenarios.
- Difficulty coverage: `d1_smoke` through `d5_stress`.
- Reference UI note: the visible reference application is styled as a consumer travel booking product; the DSL state hooks and evaluator-facing `data-testid` surface remain contract-stable.

## Reference Validation

Latest reference run:

```bash
python3 -m detoxbench evaluate-dsl \
  --target targets/web/stayflow_concierge/tier_c \
  --static-dir targets/web/stayflow_concierge/tier_c/reference_app \
  --output targets/web/stayflow_concierge/tier_c/cohorts/manual/runs/reference_all \
  --run-subject reference_all_productized \
  --headless \
  --action-timeout 3000 \
  --json
```

Result: `20260511-152750-8fd740e4`, passed `25/25` scenarios, formal score `119/119`, stepwise score `119/119`, contract score `25/25`.

## Notes

Tier C deliberately stresses multi-page navigation, service-backed quote/promo/payment/supplier flows, upload-derived joins, role-gated approvals, optimistic supplier conflict repair, persistence, and long end-to-end confirmation flows.

Blind repeat results are grouped under `cohorts/{M,T,F}/stayflow-tier-c-20260511T153500Z/`.
