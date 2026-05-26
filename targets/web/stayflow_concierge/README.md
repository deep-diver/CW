# StayFlow Concierge

StayFlow Concierge is organized as four benchmark tiers:

| Tier | Directory | Focus |
| --- | --- | --- |
| A | `tier_a/` | Single-city travel booking baseline |
| B | `tier_b/` | Multi-city concierge with ordered itinerary and role-gated ops |
| C | `tier_c/` | Trip operations command center and checkout journey |
| D | `tier_d/` | Post-confirmation release seal ledger and manager-gated release readiness |

Each tier is a complete DetoxBench DSL target. Cohort artifacts are local and
gitignored under each tier's `cohorts/{M,T,F}/` directory.

The consolidated cross-tier evaluation report is
[`evaluation_report.md`](evaluation_report.md).
