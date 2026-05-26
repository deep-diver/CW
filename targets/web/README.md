# Web Targets

The maintained target set is intentionally narrow and product-oriented:

| Suite | Tier | Directory | Pages | Scenarios |
| --- | --- | --- | ---: | ---: |
| StayFlow Concierge | A | `stayflow_concierge/tier_a/` | 3 | 23 |
| StayFlow Concierge | B | `stayflow_concierge/tier_b/` | 4 | 29 |
| StayFlow Concierge | C | `stayflow_concierge/tier_c/` | 6 | 25 |
| StayFlow Concierge | D | `stayflow_concierge/tier_d/` | 6 | 28 |
| FreshCart Market | A | `freshcart_market/tier_a/` | 3 | 24 |
| FreshCart Market | B | `freshcart_market/tier_b/` | 4 | 29 |
| FreshCart Market | C | `freshcart_market/tier_c/` | 5 | 31 |
| FreshCart Market | D | `freshcart_market/tier_d/` | 5 | 34 |
| Campus Registrar Command | A | `campus_registrar_command/tier_a/` | 3 | 24 |
| Campus Registrar Command | B | `campus_registrar_command/tier_b/` | 4 | 12 public |
| Campus Registrar Command | C | `campus_registrar_command/tier_c/` | 5 | 29 |
| Campus Registrar Command | D | `campus_registrar_command/tier_d/` | 6 | 34 |
| Media Campaign Launch Desk | A | `media_campaign_launch_desk/tier_a/` | 3 | 24 |
| Media Campaign Launch Desk | B | `media_campaign_launch_desk/tier_b/` | 4 | 12 public |
| Media Campaign Launch Desk | C | `media_campaign_launch_desk/tier_c/` | 5 | 44 |
| Media Campaign Launch Desk | D | `media_campaign_launch_desk/tier_d/` | 5 | 48 |
| Clinic Shift Command | B | `clinic_shift_command/tier_b/` | 4 | 33 |
| Clinic Shift Command | C | `clinic_shift_command/tier_c/` | 5 | 52 |
| Clinic Shift Command | D | `clinic_shift_command/tier_d/` | 5 | 55 |
| HomeFix Hub | A | `homefix_hub/tier_a/` | 3 | 24 |
| HomeFix Hub | B | `homefix_hub/tier_b/` | 4 | 29 |
| HomeFix Hub | C | `homefix_hub/tier_c/` | 5 | 31 |
| HomeFix Hub | D | `homefix_hub/tier_d/` | 6 | 34 |

Each tier directory contains the public contract, public/private scenarios,
target notes, the reference implementation, and gitignored cohort artifacts.
Blind outputs are grouped as:

```text
targets/web/<suite>/tier_<x>/cohorts/{M,T,F}/<batch-id>/
  candidates/<model>/<rep>/
  runs/<model>/<rep>/<run-id>/
```
