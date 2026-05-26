# FreshCart Market

FreshCart Market is organized as four benchmark tiers:

| Tier | Directory | Focus |
| --- | --- | --- |
| A | `tier_a/` | Fresh grocery marketplace, cart, coupon, checkout, and receipt flow |
| B | `tier_b/` | Premium multi-vendor grocery operations with fulfillment permissions |
| C | `tier_c/` | Advanced cold-chain grocery operations with restricted-item review, wallet redemption, delivery slot quoting, support tickets, and manager approvals |
| D | `tier_d/` | Micro-fulfillment dispatch manifest seal with cold-chain and manager-review gates |

Each tier is a complete DetoxBench DSL target. Cohort artifacts are local and
gitignored under each tier's `cohorts/{M,T,F}/` directory.

The consolidated cross-tier evaluation report is
[`evaluation_report.md`](evaluation_report.md).
