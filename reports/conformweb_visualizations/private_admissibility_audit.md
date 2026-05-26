# Private Scenario Admissibility Audit

This audit checks whether private scenarios stay inside the public
behavioral contract boundary. A row is marked admissible only when the private
scenario file compiles against the public contract and no raw private reference
points to an undeclared action, state path, route/page, actor, event, or
rendered table.

## Summary

- Expected target tier instances: 24
- Private scenario files present in this checkout: 22
- Private scenario files compiling against the public contract: 22/22
- Admissible present private files: 22/22
- Private scenarios audited: 485
- Private steps audited: 4317
- Compiled checks generated: 40944
- Undeclared private references found: 0

## Family Summary

| Family | Private files present | Private scenarios | Private steps | Undeclared refs |
| --- | ---: | ---: | ---: | ---: |
| Travel | 4/4 | 69 | 564 | 0 |
| Grocery | 4/4 | 93 | 668 | 0 |
| Clinical Command | 4/4 | 117 | 912 | 0 |
| Campus Registrar | 3/4 | 47 | 475 | 0 |
| Media Campaign | 3/4 | 58 | 539 | 0 |
| Home Services | 4/4 | 101 | 1159 | 0 |

## Missing Or Absent Private Files

- Campus Registrar Tier B (Operational): missing private scenario file in this checkout
- Media Campaign Tier B (Operational): missing private scenario file in this checkout

## Interpretation

The static audit supports the fairness claim that private scenarios are
contract-derived rather than hidden product requirements. Compilation is the
key check: the same compiler used to lower scenarios into browser evaluation
plans rejects references outside the public contract. This audit should be
reported together with reference-implementation validation, which establishes
that the resulting browser plans are executable by a conforming implementation.

## Generated Files

- `tables/private_admissibility_audit.csv`: full target tier audit rows.
- `tables/private_scenario_admissibility.csv`: one row per private scenario.
- `tables/private_admissibility_audit.tex`: compact Appendix table.
- `tables/private_admissibility_summary.tex`: family-level summary table.
- `tables/private_admissibility_matrix.tex`: tier matrix table.
- `figures/appendix/appendix_public_private_reference_flow.pdf`: paper-facing coverage figure.
- `figures/appendix/appendix_public_private_reference_flow_square.pdf`: square coverage figure variant.
