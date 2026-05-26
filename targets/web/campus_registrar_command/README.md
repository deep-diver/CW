# Campus Registrar Command

Campus Registrar Command is a student enrollment and advising benchmark target.
It is intentionally distinct from travel, grocery, home repair, and clinical
operations targets: the UI centers on a course catalog, schedule planning,
eligibility checks, waitlists, advisor overrides, enrollment ledgers, and degree
audit progress.

| Tier | Directory | Focus |
| --- | --- | --- |
| A | `tier_a/` | Student course planning, eligibility check, waitlist, advisor override, enrollment persistence |
| B | `tier_b/` | Degree clearance operations with section conflicts, transfer credit intake, financial/advisor/registrar role gates, waitlists, release ledger, and audit persistence |
| C | `tier_c/` | Graduation certification command with degree-audit heatmap, residency exception, aid clearance service, dean vote, registrar certification, diploma release, blocker ledger, and audit persistence |
| D | `tier_d/` | Multi-authority graduation wave command with policy epoch lock, seat arbitration, transcript/crosswalk imports, identity/bursar/diploma services, committee quorum, senate docket, provost counterseal, release wave, accreditation freeze, and manifest persistence |

Each tier is a complete DetoxBench DSL target with its own public contract,
scenario suite, and reference implementation.
