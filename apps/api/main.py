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
from core.analytics import aggregate_attribution, portfolio_summary
from core.decision_intelligence import DataQuality, Provenance, OfferLifecycle, transition_offer, attribution_weights, detect_anomalies, Economics, market_saturation, content_fatigue, allocate_portfolio, KillSwitch
from integrations.free_tools import catalog, fallback_chain
from integrations.tool_registry import ToolRegistry
from integrations.ai.model_discovery import list_free_openrouter_models
from integrations.ai.router import AIRouter
from integrations.demo import TemplateAIProvider, DryRunPublisher
from integrations.affiliate.openaffiliate import OpenAffiliateClient
from core.orchestration import AutonomousEngine
from datetime import datetime, timezone

app = FastAPI(title="AI Affiliate Engine", version="0.9.1")
policy = PolicyEngine(settings.mode, settings.max_daily_publications)
compliance = ComplianceEngine(settings.mode, settings.kill_switch, settings.max_daily_publications)
learning = LearningEngine(); store = SQLiteStore(); evolution = StrategyEvolutionEngine(); tools = ToolRegistry()
safety_switch = KillSwitch(global_enabled=not settings.kill_switch)

class ScoreRequest(BaseModel): offer: Offer; signal: Signal; country: str = "DZ"
class SimulationRequest(BaseModel): opportunity_score: float = Field(ge=0, le=100); offer: Offer; impressions: int = Field(default=10000, ge=0)
class EvaluateRequest(BaseModel): offers: list[Offer]; signals: list[Signal]; country: str = "DZ"
class MonteCarloRequest(BaseModel): offer: Offer; impressions: int = Field(default=10000, ge=0); runs: int = Field(default=1000, ge=1, le=10000); seed: int = 7
class URLRequest(BaseModel): url: str
class LearningRequest(BaseModel): opportunity_score: float = Field(ge=0, le=100); clicks: int = Field(ge=0); conversions: int = Field(ge=0); revenue: float = Field(ge=0)
class TrendRequest(BaseModel): offer: Offer; trend: TrendObservation; country: str = "DZ"
class TrendBatchRequest(BaseModel): trends: list[TrendObservation]
class StrategyRequest(BaseModel): hook: str; angle: str; format: str; audience: str; cta: str
class StrategyObservation(BaseModel): fingerprint: str; exposures: int = Field(ge=0); clicks: int = Field(ge=0); conversions: int = Field(ge=0); revenue: float = Field(ge=0); failure: bool = False
class AttributionRequest(BaseModel): rows: list[dict]
class ToolSelectionRequest(BaseModel): task: str = Field(min_length=1, max_length=300); category: str | None = None; credentials: bool | None = None
class ToolHealthRequest(BaseModel): cooldown_seconds: float = Field(default=30.0, ge=0)
class MultiTouchRequest(BaseModel): touches: list[dict]; method: str = "last_touch"; half_life: float = Field(default=7.0, gt=0)
class AnomalyRequest(BaseModel): metrics: dict[str, float]; baselines: dict[str, float]; ratio_threshold: float = Field(default=2.5, gt=1)
class EconomicsRequest(BaseModel): commission: float = Field(ge=0); refunds: float = Field(default=0, ge=0); chargebacks: float = Field(default=0, ge=0); traffic_cost: float = Field(default=0, ge=0); tool_cost: float = Field(default=0, ge=0); opportunity_cost: float = Field(default=0, ge=0); failure_probability: float = Field(default=0, ge=0, le=1)
class LifecycleRequest(BaseModel): current: OfferLifecycle; target: OfferLifecycle
class PortfolioRequest(BaseModel): expected_values: dict[str, float]; buckets: dict[str, str]; exploration_floor: float = Field(default=0.10, ge=0, le=1)
class SafetyRequest(BaseModel): scopes: list[str] = Field(default_factory=list)
class ProvenanceRequest(BaseModel): source: str; record_id: str = ""; freshness: float = Field(default=1, ge=0, le=1); completeness: float = Field(default=1, ge=0, le=1); consistency: float = Field(default=1, ge=0, le=1); source_reliability: float = Field(default=1, ge=0, le=1)
class SaturationRequest(BaseModel): trend_strength: float = Field(ge=0, le=100); competition: float = Field(ge=0, le=100); content_saturation: float = Field(ge=0, le=100); offer_quality: float = Field(ge=0, le=100)
class FatigueRequest(BaseModel): recent_exposures: int = Field(ge=0); recent_engagement_rate: float = Field(ge=0); baseline_engagement_rate: float = Field(gt=0); days_since_refresh: float = Field(ge=0)

@app.get("/health")
def health(): return {"status":"ok","mode":settings.mode.value,"kill_switch":settings.kill_switch,"version":app.version}
@app.get("/api/v1/dashboard/overview")
def dashboard_overview(): return {"system":{"mode":settings.mode.value,"kill_switch":settings.kill_switch,"version":app.version},"storage":store.stats(),"learning":learning.calibration(),"publishing":{"enabled":settings.mode != RunMode.SIMULATION,"daily_limit":settings.max_daily_publications},"providers":{"ai":"free-first adapter router","affiliate":"adapter-based","trends":"free-first public sources"},"evolution":{"strategies":len(evolution.records)},"tools":{"count":len(catalog()),"no_payment":len(catalog(only_no_payment=True,exclude_ai=True))}}
@app.get("/api/v1/capabilities")
def capabilities(): return {"modules":["scoring","research","offers","trends","opportunities","content","simulation","experiments","attribution","multi_touch_attribution","learning","evolution","portfolio","economics","anomaly_detection","saturation","fatigue","provenance","policies","analytics","persistence","free_tools","tool_registry","safety_switch"],"publishing":settings.mode != RunMode.SIMULATION,"ai_provider":"free-first adapter router","affiliate_provider":"adapter-based"}
@app.get("/api/v1/tools/free")
def free_tools(category:str|None=None,exclude_ai:bool=False): return {"policy":"free-first; quotas and provider terms still apply","tools":[x.__dict__ for x in catalog(category=category,exclude_ai=exclude_ai)],"no_payment_required":[x.__dict__ for x in catalog(category=category,only_no_payment=True,exclude_ai=exclude_ai)]}
@app.get("/api/v1/tools/registry")
def tool_registry(): return {"tools":tools.snapshot()}
@app.post("/api/v1/tools/select")
def tool_select(request:ToolSelectionRequest):
    try: return tools.select(request.task,category=request.category,credentials=request.credentials).__dict__
    except RuntimeError as exc: raise HTTPException(status_code=503,detail=str(exc))
@app.post("/api/v1/tools/{tool_id}/success")
def tool_success(tool_id:str):
    try: tools.record_success(tool_id); return {"tool":tool_id,"status":"success","health":tools.snapshot()}
    except KeyError: raise HTTPException(status_code=404,detail="unknown tool")
@app.post("/api/v1/tools/{tool_id}/failure")
def tool_failure(tool_id:str,request:ToolHealthRequest):
    try: tools.record_failure(tool_id,cooldown_seconds=request.cooldown_seconds); return {"tool":tool_id,"status":"failure","health":tools.snapshot()}
    except KeyError: raise HTTPException(status_code=404,detail="unknown tool")
@app.get("/api/v1/tools/fallback/{tool_id}")
def tool_fallback(tool_id:str):
    try: return {"tool":tool_id,"chain":fallback_chain(tool_id)}
    except KeyError: raise HTTPException(status_code=404,detail="unknown tool")
@app.get("/api/v1/ai/free-models")
def free_models():
    try: return {"source":"openrouter_catalog","models":list_free_openrouter_models()}
    except Exception as exc: raise HTTPException(status_code=503,detail=f"free model catalog unavailable: {type(exc).__name__}")
@app.get("/api/v1/ai/configured")
def configured_ai(): return {"models":AIRouter().available(),"free_first":True}
@app.post("/api/v1/opportunities/score")
def score(request:ScoreRequest): return score_offer(request.offer,request.signal,request.country)
@app.post("/api/v1/opportunities/assess")
def assess(request:TrendRequest): return assess_opportunity(request.offer,request.trend,request.country)
@app.post("/api/v1/trends/deduplicate")
def trends_deduplicate(request:TrendBatchRequest): return deduplicate_trends(request.trends)
@app.post("/api/v1/evaluate")
def evaluate_opportunities(request:EvaluateRequest): return [{"opportunity":o,"simulation":s} for o,s in evaluate(request.offers,request.signals,request.country)]
@app.post("/api/v1/simulations")
def simulation(request:SimulationRequest): return simulate(Opportunity(offer_id=request.offer.id,score=request.opportunity_score,reasons=[],risks=[],recommended=True),request.offer,request.impressions)
@app.post("/api/v1/simulations/scenarios")
def scenarios(request:SimulationRequest): return scenario_matrix(request.offer,request.impressions)
@app.post("/api/v1/simulations/monte-carlo")
def simulation_monte_carlo(request:MonteCarloRequest): return monte_carlo(request.offer,request.impressions,request.runs,request.seed)
@app.post("/api/v1/content/validate")
def content_validate(plan:ContentPlan): return validate_content(plan)
@app.post("/api/v1/security/validate-url")
def validate_url(request:URLRequest):
    try: return {"valid":True,"url":validate_public_url(request.url)}
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc))
@app.post("/api/v1/learning/observe")
def observe(request:LearningRequest): learning.record(LearningObservation(**request.model_dump())); return learning.calibration()
@app.get("/api/v1/learning/calibration")
def calibration(): return learning.calibration()
@app.post("/api/v1/evolution/register")
def evolution_register(request:StrategyRequest): record=evolution.register(StrategyGene(request.hook,request.angle,request.format,request.audience,request.cta)); return {"fingerprint":record.gene.fingerprint,"parents":record.parents}
@app.post("/api/v1/evolution/observe")
def evolution_observe(request:StrategyObservation): evolution.observe(request.fingerprint,exposures=request.exposures,clicks=request.clicks,conversions=request.conversions,revenue=request.revenue,failure=request.failure); return {"fingerprint":request.fingerprint,"value":evolution.records[request.fingerprint].value}
@app.get("/api/v1/evolution/select")
def evolution_select(min_exposures:int=50): return evolution.select(min_exposures=max(0,min_exposures))
@app.post("/api/v1/analytics/attribution")
def analytics_attribution(request:AttributionRequest): metrics=aggregate_attribution(request.rows); return {"by_key":{k:v.__dict__ for k,v in metrics.items()},"portfolio":portfolio_summary(metrics)}
@app.post("/api/v1/analytics/multi-touch")
def multi_touch(request:MultiTouchRequest): return attribution_weights(request.touches,request.method,request.half_life).__dict__
@app.post("/api/v1/analytics/anomalies")
def anomalies(request:AnomalyRequest): return {"anomalies":[x.__dict__ for x in detect_anomalies(request.metrics,request.baselines,request.ratio_threshold)]}
@app.post("/api/v1/economics")
def economics(request:EconomicsRequest): return Economics(**request.model_dump()).as_dict()
@app.post("/api/v1/offers/lifecycle")
def offer_lifecycle(request:LifecycleRequest): return {"state":transition_offer(request.current,request.target).value}
@app.post("/api/v1/portfolio/allocate")
def portfolio_allocate(request:PortfolioRequest): return allocate_portfolio(request.expected_values,request.buckets,request.exploration_floor)
@app.post("/api/v1/intelligence/saturation")
def saturation(request:SaturationRequest): return {"saturation":market_saturation(**request.model_dump())}
@app.post("/api/v1/intelligence/fatigue")
def fatigue(request:FatigueRequest): return {"fatigue":content_fatigue(**request.model_dump())}
@app.post("/api/v1/intelligence/provenance")
def provenance(request:ProvenanceRequest): return Provenance(request.source,datetime.now(timezone.utc),request.record_id,DataQuality(request.freshness,request.completeness,request.consistency,request.source_reliability)).as_dict()
@app.get("/api/v1/safety/status")
def safety_status(): return {"global_enabled":safety_switch.global_enabled,"disabled_scopes":sorted(safety_switch.disabled_scopes)}
@app.post("/api/v1/safety/disable")
def safety_disable(request:SafetyRequest):
    for scope in request.scopes: safety_switch.disable(scope)
    return safety_status()
@app.post("/api/v1/safety/enable")
def safety_enable(request:SafetyRequest):
    for scope in request.scopes: safety_switch.enable(scope)
    return safety_status()
@app.get("/api/v1/policy/publishing")
def publishing_policy(): allowed,reason=policy.can_publish(terms_verified=False,disclosure_present=False,daily_count=0); return {"allowed":allowed,"reason":reason,"mode":policy.mode.value}
@app.get("/api/v1/affiliate/openaffiliate/search")
def openaffiliate_search(q:str="",category:str|None=None,verified:bool|None=None,limit:int=20):
    try: return {"source":"openaffiliate","programs":[x.__dict__ for x in OpenAffiliateClient().search(q,category=category,verified=verified,limit=limit)]}
    except Exception as exc: raise HTTPException(status_code=503,detail=f"registry unavailable: {type(exc).__name__}")
@app.get("/api/v1/affiliate/openaffiliate/{slug}")
def openaffiliate_get(slug:str):
    try: return OpenAffiliateClient().get(slug).__dict__
    except Exception as exc: raise HTTPException(status_code=503,detail=f"registry unavailable: {type(exc).__name__}")
@app.post("/api/v1/demo/autonomous-cycle")
def autonomous_cycle(request:ScoreRequest): return AutonomousEngine(TemplateAIProvider(),DryRunPublisher(),compliance).evaluate(request.offer,request.signal,request.country)
