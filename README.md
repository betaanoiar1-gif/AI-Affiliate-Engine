# AI Affiliate OS

Provider-agnostic affiliate intelligence, experimentation, attribution and controlled automation platform.

## Operating loop
`Discover → Normalize → Score → Simulate → Select → Create → Experiment → Publish → Measure → Learn → Optimize → Evolve`

This is a closed-loop decision system, not a content generator: evidence becomes a decision, decisions become experiments, experiments create measured outcomes, and outcomes alter future strategy selection.

## Free-first architecture
The project prefers public APIs/RSS, open-source libraries and genuinely free-access paths. Paid SaaS is not a required base dependency. Credentials and provider quotas are explicit rather than hidden.

### Non-AI tools
- **Trend/research:** Hacker News public API, Google Trends RSS, Reddit RSS, YouTube/channel RSS, generic RSS/Atom, public GitHub activity and Wikimedia/Wikipedia APIs where appropriate.
- **Affiliate discovery:** optional OpenAffiliate public registry adapter for machine-readable program discovery. Registry data is treated as discovery evidence, not proof that an offer is currently available to the user's account.
- **Web acquisition:** httpx, BeautifulSoup, Trafilatura, Playwright and Crawlee for permitted public workflows. The system does not bypass access controls.
- **Media:** FFmpeg, Pillow and yt-dlp for permitted processing/metadata workflows; platform terms and content rights remain mandatory gates.
- **Data:** SQLite/WAL for operational state, DuckDB/Parquet as optional analytical storage formats, plus persistent TTL caching to reduce duplicate requests and quota consumption.
- **Quality/security:** pytest, Ruff, Bandit and pip-audit are supported as the quality/security layer.
- **Affiliate/platform:** Awin and PartnerStack remain credential-required adapters; YouTube Data API is a free-tier/credentialed surface. They are never described as unlimited/free-for-everyone.

### AI
The AI router is isolated from the non-AI tool layer and remains free-first: OpenRouter, Gemini, Groq and Hugging Face can be configured with provider-specific credentials/models. Free does **not** mean unlimited: quotas, model availability, provider terms and eligibility can change.

## Intelligence layers
- **Offer lifecycle:** discovered → verified → active → testing → winning/declining → stale/suspended/retired, with invalid transitions rejected.
- **Opportunity intelligence:** trend velocity/persistence/intent/novelty/saturation/seasonality plus risk-adjusted prioritization and hard policy vetoes.
- **Attribution:** first-touch, last-touch, linear, position-based and time-decay multi-touch attribution, kept separate from observed and predicted values.
- **Economics:** commission minus refunds, chargebacks, traffic/tool/opportunity costs, adjusted for failure probability.
- **Anomaly/fraud signals:** conservative spike/drop detection; anomalies are flagged for investigation rather than deleting evidence.
- **Portfolio allocation:** proven/emerging/exploration/experimental allocation with an explicit exploration floor instead of fixed permanent percentages.
- **Market saturation:** competition, content saturation, trend strength and offer quality are combined into a bounded pressure signal.
- **Content fatigue:** exposure, engagement deterioration and refresh age produce a bounded fatigue signal.
- **Provenance/data quality:** source, observation time, freshness, completeness, consistency and source reliability are carried as explicit evidence metadata.
- **Strategy evolution:** lineage-aware variants and controlled exploration/exploitation.
- **Replay-safe research:** point-in-time filtering prevents future information from leaking into historical evaluation.
- **Safety:** global and scoped kill switches provide an emergency stop without destroying stored evidence.

## AI-era attribution
The architecture leaves room for open Content Telemetry standards such as OpenAttribution rather than coupling the core engine to a commercial analytics vendor. OpenAttribution's v1.0 standard was published on 2 September 2026 and defines retrieval/grounding/citation/presentation/engagement event concepts; integration remains optional and the engine does not assume external telemetry is available.

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
- `/api/v1/capabilities`
- `/api/v1/tools/free`
- `/api/v1/tools/registry`
- `/api/v1/tools/select`
- `/api/v1/ai/free-models`
- `/api/v1/opportunities/score`
- `/api/v1/opportunities/assess`
- `/api/v1/simulations/monte-carlo`
- `/api/v1/analytics/attribution`
- `/api/v1/analytics/multi-touch`
- `/api/v1/analytics/anomalies`
- `/api/v1/economics`
- `/api/v1/offers/lifecycle`
- `/api/v1/portfolio/allocate`
- `/api/v1/intelligence/saturation`
- `/api/v1/intelligence/fatigue`
- `/api/v1/intelligence/provenance`
- `/api/v1/safety/status`
- `/api/v1/safety/disable`
- `/api/v1/safety/enable`
- `/api/v1/affiliate/openaffiliate/search`
- `/api/v1/affiliate/openaffiliate/{slug}`

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

GitHub Actions status must be treated as unknown when no workflow run exists; local verification should be run before claiming a green build.

## Production path
SQLite/WAL is the dependency-light persistence implementation; the service boundary is designed for PostgreSQL. Production operation still requires authentication, secret management, signed webhooks, provider-specific policy checks, observability, backups and verified OAuth credentials.

This is an automation and research platform, not a guarantee of income. Real-world results depend on offer terms, audience, traffic, platform policies and conversion performance.
