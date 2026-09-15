# AI Affiliate OS

Provider-agnostic affiliate intelligence, experimentation, content planning and controlled automation platform.

## Operating loop
`Discover → Normalize → Score → Simulate → Select → Create → Experiment → Publish → Measure → Learn → Optimize → Evolve`

The important design choice is that the system is not a content generator. It is a closed-loop decision system: evidence becomes a decision, decisions become experiments, experiments create measured outcomes, and measured outcomes alter future strategy selection.

## Intelligence layers
- **Offer intelligence:** normalize network data, commission economics, recurring potential, AOV, cookie window, terms, countries and payout compatibility.
- **Trend intelligence:** combine velocity, persistence, commercial intent, novelty, saturation and seasonality; merge duplicate signals across sources without treating them as independent evidence.
- **Opportunity engine:** transparent dimensions, hard policy vetoes, confidence based on evidence completeness, risk-adjusted prioritization and explicit reasons/risks.
- **Simulation lab:** conservative/base/optimistic scenarios and Monte Carlo uncertainty. Synthetic results are never presented as observed performance.
- **Strategy evolution:** lineage-aware variants, controlled exploration/exploitation, uncertainty bonuses and retirement/promotion hooks.
- **Attribution:** campaign/variant/content identifiers, clicks, conversions, commission and deterministic aggregate metrics such as CTR, CVR and EPC.
- **Learning:** observed outcomes are kept separate from predictions and can recalibrate future prioritization without allowing one small sample to dominate.
- **Durable workflow primitives:** explicit stages, retry state, terminal blocks and auditable transitions.

## Safety-first defaults
- Default mode is `simulation`; no external publishing is performed.
- `approval` mode prepares candidates but requires an explicit human approval step.
- `autonomous` mode is the only mode allowed to invoke a configured publisher after every compliance/content gate passes.
- Never fabricate clicks, conversions, commissions, trends, or profitability.
- Affiliate terms, country eligibility, payout information and disclosure are decision inputs, not hidden assumptions.
- External URLs are validated before provider requests.
- Secrets are supplied through environment variables and are never committed.
- Idempotent event/attribution writes prevent duplicate external events from becoming duplicate internal revenue.

## Research-informed architecture
Current research supports several design principles used here: Awin exposes publisher performance and transaction-oriented APIs, making provider adapters more valuable than screen scraping; PartnerStack exposes marketplace/program APIs and webhooks; Google is testing a programmatic Trends API with multi-year, regional and interval data; and modern agent systems increasingly separate agent reasoning from durable execution. citeturn1search7turn0search1turn0search16turn1search6

Affiliate disclosure is a first-class content/compliance concern. The FTC guidance says affiliate relationships should be disclosed clearly and conspicuously and close to the recommendation/link, and that disclosures should not be hidden in profiles or buried after the relevant content. citeturn0search0turn0search12

The system is deliberately designed to add provider adapters rather than couple the core to one network. Impact.com is another example of the direction of the ecosystem: its 2026 API catalog includes program/partner discovery, analytics, tracking links, webhooks and an MCP interface. citeturn1search2

## Architecture
- `apps/api` — FastAPI API and operational endpoints
- `apps/web` — Arabic RTL operations dashboard
- `core` — domain, intelligence, scoring, simulation, workflow, evolution, policies, compliance, persistence, learning, experiments and analytics
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
Copy `.env.example` to `.env` and keep `AFFILIATE_RUN_MODE=simulation` until provider credentials, payout compatibility, disclosure rules and publisher permissions have been verified. The application supports OpenAI-compatible AI endpoints and adapter-based affiliate/trend providers.

## Testing
```bash
python -m compileall -q core integrations apps tests
pytest -q
```

CI also runs these checks on GitHub Actions.

## Production path
SQLite/WAL is the dependency-light persistence implementation; the service boundary is designed for PostgreSQL. Before real operation, add production authentication, secret management, webhook signature verification, provider-specific policy checks, observability/alerts, backup/restore procedures and verified publisher OAuth credentials. Real publishing remains an explicit side-effect boundary.

This is an automation and research platform, not a guarantee of income. Real-world results depend on offer terms, audience, traffic, platform policies and conversion performance.
