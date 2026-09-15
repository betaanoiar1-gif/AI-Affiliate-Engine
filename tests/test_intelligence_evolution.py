from core.domain import Offer
from core.intelligence import TrendObservation, assess_opportunity, deduplicate_trends
from core.evolution import StrategyEvolutionEngine, StrategyGene


def offer(**overrides):
    data = dict(id="o1", name="Example", network="demo", commission_rate=20, average_order_value=100,
                recurring=True, cookie_days=30, payout_methods=["bank"], eligible_countries=["DZ"],
                terms_verified=True, active=True, url="https://example.com")
    data.update(overrides)
    return Offer(**data)


def test_intelligence_rewards_persistent_intent_and_flags_risk():
    trend = TrendObservation("trends", "ai tools", velocity=90, persistence=80, intent=85, novelty=70, saturation=20)
    result = assess_opportunity(offer(), trend)
    assert result.value > 50
    assert "high_commercial_intent" in result.reasons
    assert result.confidence == 1.0


def test_intelligence_blocks_ineligible_offer():
    result = assess_opportunity(offer(eligible_countries=["US"]), TrendObservation("x", "x", 90, 90, 90, 90, 10))
    assert result.value < 20
    assert "country_not_eligible" in result.risks


def test_trends_merge_without_double_counting_sources():
    merged = deduplicate_trends([TrendObservation("a", "AI", 80), TrendObservation("b", "ai", 60)])
    assert len(merged) == 1
    assert merged[0].velocity == 70


def test_strategy_evolution_register_observe_and_mutate():
    engine = StrategyEvolutionEngine(seed=1, exploration_rate=0)
    parent = engine.register(StrategyGene("hook", "angle", "short", "buyers", "cta"))
    engine.observe(parent.gene.fingerprint, exposures=100, clicks=20, conversions=5, revenue=50)
    children = engine.mutate(parent.gene.fingerprint, hooks=["hook", "new"], angles=["angle", "new"], formats=["short"], audiences=["buyers"], ctas=["cta"], count=2)
    assert len(children) == 2
    decision = engine.select(min_exposures=50)
    assert decision.selected == parent.gene.fingerprint
    assert parent.gene.fingerprint in engine.lineage(parent.gene.fingerprint)
