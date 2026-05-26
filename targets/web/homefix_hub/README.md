# HomeFix Hub

HomeFix Hub is a mass-market home repair and field-service benchmark target.
It is intentionally distinct from travel, grocery, and clinic command targets:
the UI centers on repair categories, homeowner booking, technician dispatch,
parts/material readiness, QA, insurance, and warranty completion.

| Tier | Directory | Scenarios | Visual surface |
| --- | --- | ---: | --- |
| A | `tier_a/` | 24 | Consumer home-visit booking concierge |
| B | `tier_b/` | 29 | Dark field-dispatch operations console |
| C | `tier_c/` | 31 | Blueprint-style renovation QA studio |
| D | `tier_d/` | 34 | Storm claim and warranty command room |

Each tier is independent and contains its own DSL contract, public/private
scenarios, and reference implementation. The tiers intentionally use distinct
UI/UX directions rather than a single interface that grows by adding panels.

Blind difficulty results are summarized in `evaluation_report.md`. Raw cohort
artifacts are local and gitignored under each tier's `cohorts/{M,T,F}/`
directories.
