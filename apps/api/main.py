from fastapi import FastAPI
from pydantic import BaseModel
from core.domain import Offer, Signal
from core.scoring import score_offer
from core.simulation import simulate
from core.policies import PolicyEngine
from core.pipeline import evaluate

app = FastAPI(title="AI Affiliate Engine", version="0.1.1")
policy = PolicyEngine()

class ScoreRequest(BaseModel):
    offer: Offer
    signal: Signal
    country: str = "DZ"

class SimulationRequest(BaseModel):
    opportunity_score: float
    offer: Offer
    impressions: int = 10000

class EvaluateRequest(BaseModel):
    offers: list[Offer]
    signals: list[Signal]
    country: str = "DZ"

@app.get("/health")
def health():
    return {"status": "ok", "mode": policy.mode.value, "version": app.version}

@app.get("/api/v1/capabilities")
def capabilities():
    return {"modules": ["research", "offers", "scoring", "content", "simulation", "policies", "analytics"], "publishing": False, "ai_provider": "adapter-based", "affiliate_provider": "adapter-based"}

@app.post("/api/v1/opportunities/score")
def score(request: ScoreRequest):
    return score_offer(request.offer, request.signal, request.country)

@app.post("/api/v1/evaluate")
def evaluate_opportunities(request: EvaluateRequest):
    return [{"opportunity": o, "simulation": s} for o, s in evaluate(request.offers, request.signals, request.country)]

@app.post("/api/v1/simulations")
def simulation(request: SimulationRequest):
    from core.domain import Opportunity
    opportunity = Opportunity(offer_id=request.offer.id, score=request.opportunity_score, reasons=[], risks=[], recommended=True)
    return simulate(opportunity, request.offer, request.impressions)

@app.get("/api/v1/policy/publishing")
def publishing_policy():
    allowed, reason = policy.can_publish(terms_verified=False, disclosure_present=False, daily_count=0)
    return {"allowed": allowed, "reason": reason, "mode": policy.mode.value}
