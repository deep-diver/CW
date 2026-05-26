# StayFlow Concierge Tier A

StayFlow Concierge Tier A is the baseline paper-target candidate for a
consumer travel booking and concierge workflow.

This target is intentionally scoped as the first tier in the StayFlow family:

- **Tier A:** current target. Three-route booking flow with catalog filtering,
  stay selection, add-on pricing, promo service validation, guest validation,
  CSV group manifest upload, agent role confirmation, reload persistence, and
  browser history checks.
- **Tier B/C:** future target variants are expected to increase state-space,
  cross-page coupling, service dependencies, and scenario length while
  preserving the same clean-room blind evaluation discipline.

Blind implementations must receive the DSL contract only. They must not receive
the reference implementation, public scenarios, private scenarios, evaluator
logs, or screenshots. Generation prompts may require production-quality,
domain-appropriate UI/UX because visual realism is part of the paper-facing
target quality, but those prompts must not reveal scenario answers.

Reference implementation status:

- Contract compilation: passing
- Public/private evaluator run: 23 / 23 scenarios passing
- DSL version: 3.0.0

## Paper Baseline Status

StayFlow Concierge Tier A is the first target that follows the current
paper-target development method:

1. design a realistic service application;
2. author the public DSL 3.0 contract and tiered public/private scenarios;
3. compile the contract and scenarios into a deterministic evaluator;
4. build a productized reference app that passes all scenarios;
5. generate blind implementations from the public contract only, while asking
   for similarly polished domain-appropriate UI/UX;
6. evaluate a ladder of weaker, upper, and frontier models.

The blind implementations did not receive the reference source, reference
screenshots, public/private scenario files, evaluator logs, or failure answers.

## Scenario Shape

The Tier A evaluator currently contains 23 scenarios across these tiers:

| Tier | Scenarios |
| --- | ---: |
| smoke | 2 |
| core | 4 |
| validation | 3 |
| service | 4 |
| upload | 2 |
| permission | 2 |
| persistence | 4 |
| journey | 2 |

## Cohort Summary

| Cohort | Subject | Scenarios | Formal | Stepwise | Contract |
| --- | --- | ---: | ---: | ---: | ---: |
| Reference | `reference_all` | 23 / 23 | 100% | 100% | 100% |
| Lower | `blind_gpt54_nano_01` | 17 / 23 | 71% | 85% | 78% |
| Lower | `blind_claude_haiku45_01` | 0 / 23 | 0% | 10% | 100% |
| Lower | `blind_gemini31_flash_lite_01` | 0 / 23 | 0% | 10% | 100% |
| Upper | `blind_gpt54_mini_01` | 0 / 23 | 0% | 10% | 100% |
| Upper | `blind_claude_sonnet46_01` | 13 / 23 | 54% | 82% | 78% |
| Upper | `blind_gemini_flash_latest_01` | 0 / 23 | 0% | 10% | 100% |
| Frontier | `blind_gpt54_01` | 17 / 23 | 70% | 85% | 78% |
| Frontier | `blind_claude_opus46_01` | 17 / 23 | 73% | 85% | 78% |
| Frontier | `blind_gemini31_pro_preview_01` | 7 / 23 | 28% | 67% | 39% |

## Observed Difficulty Signal

The strongest recurring failure is UI actionability under realistic product
flows. Several blind apps create required controls in the DOM but hide them
when later scenarios need to click or fill them. This is not a private-answer
failure: the contract exposes the component identity, but the implementation
does not keep that public behavior surface usable across the required route and
state combinations.

Other recurring failures include raw table-cell formatting mismatches, repeated
service-call terminal state mistakes, and route persistence mistakes after page
reload.

## Related Records

- Global method note: `docs/paper-target-development-method.md`
- Lower cohort: `cohort-tier-a-lower-models.md`
- Upper cohort: `cohort-tier-a-upper-models.md`
- Frontier cohort: `cohort-tier-a-frontier-models.md`
