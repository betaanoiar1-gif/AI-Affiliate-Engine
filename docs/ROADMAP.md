# Engineering roadmap

The roadmap is execution-oriented: completed items are implemented in code, not placeholders.

## Phase 1 — foundation
- [x] Domain models
- [x] Transparent scoring
- [x] Deterministic simulation
- [x] Central policy gates
- [x] Provider interfaces
- [x] Safe dry-run adapters
- [x] API + dashboard skeleton
- [x] Automated tests / CI

## Phase 2 — intelligence
- [x] Persistent SQLite event store
- [ ] Production affiliate/network ingestion adapters
- [ ] Production trend-source adapters
- [x] Opportunity evaluation pipeline
- [x] Explainable risk-aware ranking
- [x] Experiment registry primitives

## Phase 3 — content
- [x] Provider-agnostic AI/content interface
- [ ] AI router with quota/cost controls
- [x] Content briefs and platform field model
- [x] Disclosure/compliance gates
- [ ] Content quality and semantic duplication service

## Phase 4 — operations
- [x] Guarded orchestration cycle
- [x] Attribution primitives and reconciliation boundary
- [x] Retry, circuit-breaker and rate-limiter primitives
- [x] SSRF-safe URL validation
- [ ] Persistent job queue / scheduler
- [ ] Production publisher adapters
- [ ] Provider webhook ingestion
- [ ] Full audit-log service and operational kill-switch persistence

## Phase 5 — autonomous optimization
- [x] Adaptive multi-armed experiment primitive
- [x] Feedback learning/calibration primitive
- [ ] Persistent learning feature store
- [ ] Budget/rate-limit aware planner
- [x] Human approval boundary for irreversible publishing
- [x] End-to-end dry-run cycle
- [ ] Production-grade autonomous loop after external credentials and policy verification

## Phase 6 — hardening
- [ ] Database migrations and PostgreSQL adapter
- [ ] Full authentication / RBAC
- [ ] Observability, metrics and tracing
- [ ] Contract tests for every external provider
- [ ] Failure-injection suite
- [ ] Release packaging and deployment manifests

No live publisher or affiliate credential is enabled by default. External integrations are capability-gated and must never bypass compliance or simulation controls.
