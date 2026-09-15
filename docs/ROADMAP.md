# Engineering roadmap

## Completed engineering layers
- [x] Domain models and transparent opportunity scoring
- [x] Deterministic, scenario and Monte Carlo simulation lab
- [x] Central policy/compliance gates and kill switch
- [x] Persistent SQLite event/intelligence store
- [x] Attribution and commission reconciliation primitives
- [x] Experiment engine and feedback calibration
- [x] Reliability primitives: retry, circuit breaker, rate limiter
- [x] SSRF-aware URL validation and secret redaction
- [x] Provider interfaces and dry-run adapters
- [x] Awin publisher read adapter
- [x] PartnerStack partner read adapter
- [x] OpenAI-compatible cost-aware AI router
- [x] Operator-configured RSS trend adapter
- [x] FastAPI service and dashboard foundation
- [x] Compile/test CI gate

## Next engineering layers
- [ ] Offer ingestion service with normalization, deduplication and freshness TTL
- [ ] Multi-source trend fusion, velocity, persistence, seasonality and saturation
- [ ] Content factory with structured AI outputs, quality gates and duplicate detection
- [ ] Experiment registry persistence and statistically safer promotion/retirement rules
- [ ] End-to-end attribution IDs, webhook ingestion and revenue reconciliation
- [ ] Scheduler/worker loop for discover → score → simulate → create → measure → learn
- [ ] YouTube publisher adapter with explicit OAuth/approval and private-by-default safeguards
- [ ] Provider health, quotas, observability and audit dashboards
- [ ] Full API integration/security/failure-injection test suite
- [ ] PostgreSQL deployment profile and migrations for larger workloads

## Operating modes
- `simulation`: default; no external publishing
- `approval`: content can be prepared, irreversible actions require approval
- `autonomous`: only for explicitly configured providers and after policy checks

Real credentials, platform authorization, affiliate-program acceptance and provider-specific terms remain external prerequisites. The system must never represent synthetic simulation output as real performance.
