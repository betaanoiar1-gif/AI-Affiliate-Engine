from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from core.domain import Offer, Signal, Opportunity, RunMode, ContentPlan
from core.scoring import score_offer
from core.simulation import simulate, scenario_matrix, monte_carlo
from core.policies import PolicyEngine
from core.pipeline import evaluate
from core.config import settings
from core.compliance import ComplianceEngine
from core.learning import LearningEngine, LearningObservation
from core.security import validate_public_url
from core.content import validate_content
from core.store import SQLiteStore
from core.intelligence import TrendObservation, assess_opportunity, deduplicate_trends
from core.evolution import StrategyEvolutionEngine, StrategyGene
from integrations.free_tools import catalog, fallback_chain
from integrations.ai.model_discovery import list_free_openrouter_models
from integrations.ai.router import AIRouter
from integrations.demo import TemplateAIProvider, DryRunPublisher
from core.orchestration import AutonomousEngine

app = FastAPI(title="AI Affiliate Engine", version="0.7.0")
policy = PolicyEngine(settings.mode, settings.max_daily_publications)
compliance = ComplianceEngine(settings.mode, settings.kill_switch, settings.max_daily_publications)
learning = LearningEngine()
store = SQLiteStore()
evolution = StrategyEvolutionEngine()

class ScoreRequest(BaseModel):
    offer: Offer
    signal: Signal
    country: str = "DZ"

class SimulationRequest(BaseModel):
    opportunity_score: float = Field(ge=0, le=100)
    offer: Offer
    impressions: int = Field(default=10000, ge=0)

class EvaluateRequest(BaseModel):
    offers: list[Offer]
    signals: list[Signal]
    country: str = "DZ"

class MonteCarloRequest(BaseModel):
    offer: Offer
    impressions: int = Field(default=10000, ge=0)
    runs: int = Field(default=1000, ge=1, le=10000)
    seed: int = 7

class URLRequest(BaseModel):
    url: str

class LearningRequest(BaseModel):
    opportunity_score: float = Field(ge=0, le=100)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)
    revenue: float = Field(ge=0)

class TrendRequest(BaseModel):
    offer: Offer
    trend: TrendObservation
    country: str = "DZ"

class TrendBatchRequest(BaseModel):
    trends: list[TrendObservation]

class StrategyRequest(BaseModel):
    hook: str
    angle: str
    format: str
    audience: str
    cta: str

class StrategyObservation(BaseModel):
    fingerprint: str
    exposures: int = Field(ge=0)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)
    revenue: float = Field(ge=0)
    failure: bool = False

class AttributionRequest(BaseModel):
    rows: list[dict]

@app.get("/health")
def health():
    return {"status": "ok", "mode": settings.mode.value, "kill_switch": settings.kill_switch, "version": app.version}

@app.get("/api/v1/dashboard/overview")
def dashboard_overview():
    return {"system": {"mode": settings.mode.value, "kill_switch": settings.kill_switch, "version": app.version}, "storage": store.stats(), "learning": learning.calibration(), "publishing": {"enabled": settings.mode != RunMode.SIMULATION, "daily_limit": settings.max_daily_publications}, "providers": {"ai": "free-first adapter router", "affiliate": "adapter-based", "trends": "free-first public sources"}, "evolution": {"strategies": len(evolution.records)}}

@app.get("/api/v1/capabilities")
def capabilities():
    return {"modules": ["scoring", "research", "offers", "trends", "opportunities", "content", "simulation", "experiments", "attribution", "learning", "evolution", "policies", "analytics", "persistence", "free_tools"], "publishing": settings.mode != RunMode.SIMULATION, "ai_provider": "free-first adapter router", "affiliate_provider": "adapter-based"}

@app.get("/api/v1/tools/free")
def free_tools(category: str | None = None):
    return {"policy": "free-first; quotas and provider terms still apply", "tools": [x.__dict__ for x in catalog(category=category)], "no_payment_required": [x.__dict__ for x in catalog(category=category, only_no_payment=True)]}

@app.get("/api/v1/tools/fallback/{tool_id}")
def tool_fallback(tool_id: str):
    try:
        return {"tool": tool_id, "chain": fallback_chain(tool_id)}
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown tool")

@app.get("/api/v1/ai/free-models")
def free_models():
    try:
        return {"source": "openrouter_catalog", "models": list_free_openrouter_models()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"free model catalog unavailable: {type(exc).__name__}")

@app.get("/api/v1/ai/configured")
def configured_ai():
    return {"models": AIRouter().available(), "free_first": True}

@app.post("/api/v1/opportunities/score")
def score(request: ScoreRequest):
    return score_offer(request.offer, request.signal, request.country)

@app.post("/api/v1/opportunities/assess")
def assess(request: TrendRequest):
    return assess_opportunity(request.offer, request.trend, request.country)

@app.post("/api/v1/trends/deduplicate")
def trends_deduplicate(request: TrendBatchRequest):
    return deduplicate_trends(request.trends)

@app.post("/api/v1/evaluate")
def evaluate_opportunities(request: EvaluateRequest):
    return [{"opportunity": o, "simulation": s} for o, s in evaluate(request.offers, request.signals, request.country)]

@app.post("/api/v1/simulations")
def simulation(request: SimulationRequest):
    opportunity = Opportunity(offer_id=request.offer.id, score=request.opportunity_score, reasons=[], risks=[], recommended=True)
    return simulate(opportunity, request.offer, request.impressions)

@app.post("/api/v1/simulations/scenarios")
def scenarios(request: SimulationRequest):
    return scenario_matrix(request.offer, request.impressions)

@app.post("/api/v1/simulations/monte-carlo")
def simulation_monte_carlo(request: MonteCarloRequest):
    return monte_carlo(request.offer, request.impressions, request.runs, request.seed)

@app.post("/api/v1/content/validate")
def content_validate(plan: ContentPlan):
    return validate_content(plan)

@app.post("/api/v1/security/validate-url")
def validate_url(request: URLRequest):
    try:
        return {"valid": True, "url": validate_public_url(request.url)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/v1/learning/observe")
def observe(request: LearningRequest):
    learning.record(LearningObservation(**request.model_dump()))
    return learning.calibration()

@app.get("/api/v1/learning/calibration")
def calibration():
    return learning.calibration()

@app.post("/api/v1/evolution/register")
def evolution_register(request: StrategyRequest):
    record = evolution.register(StrategyGene(request.hook, request.angle, request.format, request.audience, request.cta))
    return {"fingerprint": record.gene.fingerprint, "parents": record.parents}

@app.post("/api/v1/evolution/observe")
def evolution_observe(request: StrategyObservation):
    evolution.observe(request.fingerprint, exposures=request.exposures, clicks=request.clicks, conversions=request.conversions, revenue=request.revenue, failure=request.failure)
    return {"fingerprint": request.fingerprint, "value": evolution.records[request.fingerprint].value}

@app.get("/api/v1/evolution/select")
def evolution_select(min_exposures: int = 50):
    return evolution.select(min_exposures=max(0, min_exposures))

@app.get("/api/v1/policy/publishing")
def publishing_policy():
    allowed, reason = policy.can_publish(terms_verified=False, disclosure_present=False, daily_count=0)
    return {"allowed": allowed, "reason": reason, "mode": policy.mode.value}

@app.post("/api/v1/demo/autonomous-cycle")
def autonomous_cycle(request: ScoreRequest):
    engine = AutonomousEngine(TemplateAIProvider(), DryRunPublisher(), compliance)
    return engine.evaluate(request.offer, request.signal, request.country)
