from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from core.domain import Offer, Signal, Opportunity, RunMode
from core.scoring import score_offer
from core.simulation import simulate, scenario_matrix, monte_carlo
from core.policies import PolicyEngine
from core.pipeline import evaluate
from core.config import settings
from core.compliance import ComplianceEngine
from core.experiments import Experiment
from core.attribution import create_click, conversion_from_click, summarize
from core.learning import LearningEngine, LearningObservation
from core.security import validate_public_url
from integrations.demo import TemplateAIProvider, DryRunPublisher
from core.orchestration import AutonomousEngine

app = FastAPI(title="AI Affiliate Engine", version="0.2.0")
policy = PolicyEngine(settings.mode, settings.max_daily_publications)
compliance = ComplianceEngine(settings.mode, settings.kill_switch, settings.max_daily_publications)
learning = LearningEngine()


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


@app.get("/health")
def health():
    return {"status": "ok", "mode": settings.mode.value, "kill_switch": settings.kill_switch, "version": app.version}


@app.get("/api/v1/capabilities")
def capabilities():
    return {"modules": ["research", "offers", "scoring", "content", "simulation", "experiments", "attribution", "learning", "policies", "analytics"], "publishing": settings.mode != RunMode.SIMULATION, "ai_provider": "adapter-based", "affiliate_provider": "adapter-based"}


@app.post("/api/v1/opportunities/score")
def score(request: ScoreRequest):
    return score_offer(request.offer, request.signal, request.country)


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


@app.get("/api/v1/policy/publishing")
def publishing_policy():
    allowed, reason = policy.can_publish(terms_verified=False, disclosure_present=False, daily_count=0)
    return {"allowed": allowed, "reason": reason, "mode": policy.mode.value}


@app.post("/api/v1/demo/autonomous-cycle")
def autonomous_cycle(request: ScoreRequest):
    engine = AutonomousEngine(TemplateAIProvider(), DryRunPublisher(), compliance)
    result = engine.evaluate(request.offer, request.signal, request.country)
    return result
