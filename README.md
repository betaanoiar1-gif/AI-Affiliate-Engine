# AI Affiliate OS

Provider-agnostic affiliate intelligence, experimentation, content planning and controlled automation platform.

## Operating loop
`Discover → Normalize → Score → Simulate → Select → Create → Experiment → Publish → Measure → Learn → Optimize → Evolve`

This is a closed-loop decision system, not a content generator: evidence becomes a decision, decisions become experiments, experiments create measured outcomes, and outcomes alter future strategy selection.

## Free-first tool strategy
The project has a provider-neutral registry and fallback chains. The base stack avoids paid SaaS dependencies whenever a public API, RSS feed, open-source library, or genuinely free-access path can do the job.

### Non-AI tools
- **Trend/research:** Hacker News public API, Google Trends RSS, Reddit RSS, YouTube/channel RSS, generic RSS/Atom, public GitHub activity, Wikimedia/Wikipedia APIs where appropriate.
- **Web acquisition:** httpx, BeautifulSoup, Trafilatura, Playwright and Crawlee for permitted public workflows. The system does not bypass access controls.
- **Media:** FFmpeg, Pillow and yt-dlp for permitted processing/metadata workflows; platform terms and content rights remain mandatory gates.
- **Data:** SQLite/WAL for operational state, DuckDB/Parquet as optional analytical storage formats, and a persistent TTL cache to reduce duplicate requests and quota consumption.
- **Quality/security:** pytest, Ruff, Bandit and pip-audit are supported as the local quality/security layer; they are not runtime dependencies of the API.
- **Affiliate/platform:** Awin and PartnerStack remain credential-required adapters; YouTube Data API is a free-tier/credentialed surface. They are never described as unlimited/free-for-everyone.

### AI
The AI router is separate from the non-AI tool layer and is free-first: OpenRouter, Gemini, Groq and Hugging Face can be configured with provider-specific credentials/models, with dynamic free-model discovery where supported. Free does **not** mean unlimited: quotas, model availability, provider terms and eligibility can change.

### Tool economy
`Task → eligible tools → cost/credential filter → health → selection → fallback`

Temporary failures put a tool into a short cooldown instead of repeatedly hammering the same provider. This prevents one unavailable service from stopping the whole research loop and helps conserve free quotas.

## Intelligence layers
- **Offer intelligence:** commission economics, recurring potential, AOV, cookie window, terms, countries and payout compatibility.
- **Trend intelligence:** velocity, persistence, commercial intent, novelty, saturation and seasonality.
- **Opportunity engine:** transparent dimensions, confidence, risk-adjusted prioritization and hard policy vetoes.
- **Simulation lab:** conservative/base/optimistic scenarios and Monte Carlo uncertainty; synthetic results never become observed performance.
- **Strategy evolution:** lineage-aware variants and controlled exploration/exploitation.
- **Attribution:** campaign/variant/content identifiers, clicks, conversions, commission, CTR, CVR and EPC.
- **Learning:** observed outcomes remain separate from predictions and small samples cannot dominate future decisions.

## Safety-first defaults
- Default mode is `simulation`; no external publishing is performed.
- `approval` requires explicit human approval.
- `autonomous` can invoke a configured publisher only after every compliance/content gate passes.
- Never fabricate clicks, conversions, commissions, trends, or profitability.
- Secrets stay in environment variables.
- External URLs are validated and redirects are disabled at provider boundaries.
- Provider failures should degrade to the next configured free/approved fallback rather than silently invent data.

## API
- `/health`
- `/api/v1/dashboard/overview`
- `/api/v1/tools/free`
- `/api/v1/tools/registry`
- `/api/v1/tools/select`
- `/api/v1/tools/fallback/{tool_id}`
- `/api/v1/ai/free-models`
- `/api/v1/ai/configured`
- `/api/v1/opportunities/score`
- `/api/v1/opportunities/assess`
- `/api/v1/simulations/monte-carlo`
- `/api/v1/analytics/attribution`

## Quick start
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
```

Dashboard: `/`  
API docs: `/docs`

## Configuration
Copy `.env.example` to `.env`. Keep `AFFILIATE_RUN_MODE=simulation` until provider credentials, payout compatibility, disclosure rules and publisher permissions are verified.

## Testing
```bash
python -m compileall -q core integrations apps tests
pytest -q
```

## Production path
SQLite/WAL is the dependency-light persistence implementation; the service boundary is designed for PostgreSQL. Production operation still requires authentication, secret management, signed webhooks, provider-specific policy checks, observability, backups and verified OAuth credentials.

This is an automation and research platform, not a guarantee of income. Real-world results depend on offer terms, audience, traffic, platform policies and conversion performance.
