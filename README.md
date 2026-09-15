# AI Affiliate OS

Provider-agnostic affiliate intelligence, experimentation, content planning and controlled automation platform.

## Operating loop
`Discover → Normalize → Score → Simulate → Select → Create → Experiment → Publish → Measure → Learn → Optimize → Evolve`

This is a closed-loop decision system, not a content generator: evidence becomes a decision, decisions become experiments, experiments create measured outcomes, and outcomes alter future strategy selection.

## Free-first tool strategy
The project now has a provider-neutral free-tool registry and fallback chains. The base stack avoids paid SaaS dependencies whenever a public API, RSS feed, open-source library, or free provider tier can do the job.

### Research / trends
- Hacker News official public API — no key; useful for technology/product demand signals.
- Google Trends public RSS feeds — no paid API dependency for the base trend-discovery path.
- Reddit RSS feeds — no API key for feed-based discovery where the feed is available and permitted.
- YouTube/channel RSS where available — lightweight discovery fallback before spending API quota.
- Generic RSS/Atom — universal fallback for publishers and niche sources.
- Google Trends official API is kept as an optional future adapter because its current access is an alpha program rather than a universally open API.

### AI
The router is now free-first and supports separate credentials/models for OpenRouter, Gemini, Groq and Hugging Face, plus an explicit custom OpenAI-compatible fallback. OpenRouter free-model selection is discovered dynamically from its current catalog instead of hardcoding a model that may later stop being free.

Free does **not** mean unlimited: quotas, model availability, provider terms and eligibility can change. The system therefore treats free providers as interchangeable resources with fallback and budget controls.

### Browser / media
Playwright and Crawlee are available as open-source automation/crawling choices. yt-dlp is available for permitted metadata/media workflows; platform terms and content rights remain mandatory gates.

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
