# Model Tiers

Date: 2026-05-11

DetoxBench reports model cohorts with a small, fixed tier vocabulary. This is
orthogonal to target difficulty tiers such as StayFlow Concierge Tier A/B and
scenario difficulty tiers such as smoke, core, validation, service, upload,
permission, persistence, and journey.

| Model Tier | Meaning | Models |
| --- | --- | --- |
| M | Mini cohort | GPT 5.4 nano (`gpt-5.4-nano`), Claude Haiku 4.5 (`claude-haiku-4-5`), Gemini 3.1 Flash Light/Lite (`gemini-3.1-flash-lite`) |
| T | Turbo cohort | GPT 5.4 mini (`gpt-5.4-mini`), Claude Sonnet 4.6 (`claude-sonnet-4-6`), Gemini Flash latest proxy (`gemini-flash-latest`) |
| F | Frontier cohort | GPT 5.4 (`gpt-5.4`), Claude Opus 4.6 (`claude-opus-4-6`), Gemini 3.1 Pro Preview (`gemini-3.1-pro-preview`) |

Blind implementation reports should record:

- the model tier (`M`, `T`, or `F`);
- the requested provider model id;
- the actually resolved model id when a provider aliases or falls back;
- whether the candidate received only the public contract and product-quality
  UI/UX instruction;
- formal score, stepwise score, contract score, scenario-tier breakdown, and
  first-failure category.

The T-tier Google slot is fixed to `gemini-flash-latest`. This intentionally
replaces the earlier `gemini-3.1-flash` label because the current Google
Generative Language API model list does not expose `gemini-3.1-flash` for
`generateContent`.

If a provider aliases a model id, the run remains useful only if the report
explicitly records the resolved model id. The public paper table should
distinguish requested and actual model ids when those differ.
