# Blind Private Scenario Pass Investigation

This note checks whether blind generated implementations passed private scenarios despite generation prompts not including private scenario files.

## Prompt boundary

- `tools/generate_blind_dsl_static_app.py` prompts generation from a public contract only and says not to assume access to hidden evaluator scenarios.
- Its CLI accepts `--public-scenarios-dsl`; the help text states that private scenarios must not be supplied.

## Latest reported aggregate

The reported rollup `full_pass` is stricter than private-only success: it counts blind generated runs that pass all scoring scenarios in the reported evaluation. Because private scoring scenarios are included, these runs necessarily passed the private scenarios as well.

- Overall: 244/2157 (11.3%) full pass on the realized denominator; planned denominator is 244/2,160 (11.3%).

| Family | Full-pass blind runs |
|---|---:|
| Travel | 6/359 (1.7%) |
| Grocery | 20/359 (5.6%) |
| Clinical Command | 43/360 (11.9%) |
| Campus Registrar | 70/360 (19.4%) |
| Media Campaign | 86/359 (24.0%) |
| Home Services | 19/360 (5.3%) |

| Tier | Full-pass blind runs |
|---|---:|
| Tier A | 116/539 (21.5%) |
| Tier B | 82/540 (15.2%) |
| Tier C | 38/539 (7.1%) |
| Tier D | 8/539 (1.5%) |

| Model group | Full-pass blind runs |
|---|---:|
| Mini | 5/719 (0.7%) |
| Turbo | 65/720 (9.0%) |
| Frontier | 174/718 (24.2%) |

## Latest aggregate by family and tier

| Family | A | B | C | D |
|---|---:|---:|---:|---:|
| Travel | 2/90 | 2/90 | 1/89 | 1/90 |
| Grocery | 12/89 | 3/90 | 4/90 | 1/90 |
| Clinical Command | 23/90 | 13/90 | 5/90 | 2/90 |
| Campus Registrar | 31/90 | 30/90 | 6/90 | 3/90 |
| Media Campaign | 37/90 | 28/90 | 20/90 | 1/89 |
| Home Services | 11/90 | 6/90 | 2/90 | 0/90 |

## Raw-trace private-only recomputation

The raw scenario table currently contains paper-main traces for four families: Clinic Shift Command, FreshCart Market, HomeFix Hub, and StayFlow Concierge. On this subset we can recompute private-only success directly from scenario visibility.

- Raw subset runs: 1163
- Private-only all-pass runs: 98/1163 (8.4%)
- Public+private all-pass runs: 84/1163 (7.2%)
- Private all-pass but public not all-pass: 14

| Raw family | Private all-pass | Public+private all-pass |
|---|---:|---:|
| Clinic Shift Command | 41/270 | 41/270 |
| FreshCart Market | 21/269 | 19/269 |
| HomeFix Hub | 27/357 | 19/357 |
| StayFlow Concierge | 9/267 | 5/267 |

| Raw tier | Private all-pass | Public+private all-pass |
|---|---:|---:|
| Tier A | 54/357 | 48/357 |
| Tier B | 30/360 | 24/360 |
| Tier C | 14/358 | 12/358 |
| Tier D | 0/88 | 0/88 |

| Raw model group | Private all-pass | Public+private all-pass |
|---|---:|---:|
| Mini | 0/389 | 0/389 |
| Turbo | 30/390 | 24/390 |
| Frontier | 68/384 | 60/384 |

| Raw model | Private all-pass | Public+private all-pass |
|---|---:|---:|
| Claude Opus 4.6 | 25/129 | 24/129 |
| GPT-5.4 | 22/127 | 16/127 |
| Gemini 3.1 Pro Preview | 21/128 | 20/128 |
| Claude Haiku 4.5 | 0/129 | 0/129 |
| GPT-5.4 nano | 0/130 | 0/130 |
| Gemini 3.1 Flash Lite | 0/130 | 0/130 |
| Claude Sonnet 4.6 | 15/130 | 15/130 |
| Gemini 3.1 Flash | 13/130 | 7/130 |
| GPT-5.4 mini | 2/130 | 2/130 |

## Private pass but public fail

There are 14 raw-subset runs that pass every private scenario but fail at least one public scenario. This confirms that private-only success is not identical to full-pass accounting.

| Family | Tier | Model group | Model | Run id |
|---|---|---|---|---|
| FreshCart Market | A | T | Gemini 3.1 Flash | `20260512-035539-97615d1e` |
| FreshCart Market | A | T | Gemini 3.1 Flash | `20260512-035615-d93beadc` |
| HomeFix Hub | B | F | GPT-5.4 | `20260514-030623-b104f379` |
| HomeFix Hub | B | F | GPT-5.4 | `20260514-030712-23f2c559` |
| HomeFix Hub | B | T | Gemini 3.1 Flash | `20260514-030338-17ae086a` |
| HomeFix Hub | B | T | Gemini 3.1 Flash | `20260514-030401-68004542` |
| HomeFix Hub | B | T | Gemini 3.1 Flash | `20260514-030430-3becfe6a` |
| HomeFix Hub | B | T | Gemini 3.1 Flash | `20260514-030529-de6b1ebd` |
| HomeFix Hub | C | F | Claude Opus 4.6 | `20260514-101558-17869329` |
| HomeFix Hub | C | F | GPT-5.4 | `20260514-100934-6d624bbd` |
| StayFlow Concierge | A | F | Gemini 3.1 Pro Preview | `20260511-131522-abd145ba` |
| StayFlow Concierge | A | F | GPT-5.4 | `20260511-130622-33687bd5` |
| StayFlow Concierge | A | F | GPT-5.4 | `20260511-130656-487ed4fa` |
| StayFlow Concierge | A | F | GPT-5.4 | `20260511-130836-d79e48bc` |

## Interpretation

- Yes: the records contain blind implementations that passed private scenarios without receiving private scenario files during generation.
- The strongest latest aggregate evidence is 244 full-pass reported runs, because those runs pass the full scoring set and therefore pass private scoring scenarios as well.
- The direct private-only recomputation is available for the current raw-trace subset and finds 98 private-only all-pass runs, including 14 that were not full public+private passes.
- Raw private-only recomputation is currently limited to the families with raw scenario traces present locally; aggregate rollups cover all six families.