# AI Affiliate Engine

Autonomous, provider-agnostic affiliate intelligence and content operations platform.

## Principles
- Discover opportunities before creating content.
- Score offers with transparent, testable rules.
- Simulate before publishing.
- Respect affiliate-program and platform policies.
- Never fabricate clicks, conversions, commissions, or profitability.
- Keep AI providers, affiliate networks, trend sources, and publishers behind adapters.

## Architecture
`Sources → Research → Opportunity Scoring → Content Planning → Simulation → Publishing → Analytics → Learning`

## Monorepo
- `apps/api` — FastAPI service
- `apps/web` — dashboard foundation
- `core` — domain models, scoring, policies
- `integrations` — provider interfaces and adapters
- `tests` — deterministic tests
- `.github/workflows` — CI

## Quick start
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

Open `/docs` for API documentation.

## Safety
This is an automation and research platform, not a guarantee of income. Real publishing remains disabled until credentials, program terms, disclosure requirements, rate limits, and payout eligibility are verified.
