# AI Affiliate OS

Provider-agnostic affiliate intelligence, experimentation, content planning and controlled automation platform.

## Operating loop
`Discover → Normalize → Score → Simulate → Create → Experiment → Publish → Measure → Learn → Optimize`

## Safety-first defaults
- Default mode is `simulation`; no external publishing is performed.
- `approval` mode prepares candidates but requires an explicit human approval step.
- `autonomous` mode is the only mode allowed to invoke a configured publisher after every compliance/content gate passes.
- Never fabricate clicks, conversions, commissions, trends, or profitability.
- Affiliate terms, country eligibility, payout information and disclosure are treated as decision inputs.
- External URLs are validated before provider requests.
- Secrets are supplied through environment variables and are never committed.

## Architecture
- `apps/api` — FastAPI API and operational endpoints
- `apps/web` — Arabic RTL operations dashboard
- `core` — domain, scoring, simulation, policies, compliance, persistence, learning, experiments
- `integrations` — affiliate, AI, trend and publishing adapters
- `tests` — deterministic unit and API contract tests
- `.github/workflows` — CI on push/PR plus manual dispatch

## Quick start
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

Dashboard: `/`  
API docs: `/docs`  
Health: `/health`  
Operational overview: `/api/v1/dashboard/overview`

## Configuration
Copy `.env.example` to `.env` and keep `AFFILIATE_RUN_MODE=simulation` until provider credentials and policies have been verified. The application supports OpenAI-compatible AI endpoints and adapter-based affiliate/trend providers.

## Testing
```bash
python -m compileall -q core integrations apps tests
pytest -q
```

CI also runs these checks on GitHub Actions.

## Production path
The current persistence boundary uses SQLite/WAL for a dependency-light deployment and is designed to be replaced by PostgreSQL. Before real operation, add production authentication, secret management, webhook signature verification, provider-specific policy checks, observability/alerts, backup/restore procedures, and verified publisher OAuth credentials.

This is an automation and research platform, not a guarantee of income. Real-world results depend on offer terms, audience, traffic, platform policies and conversion performance.
