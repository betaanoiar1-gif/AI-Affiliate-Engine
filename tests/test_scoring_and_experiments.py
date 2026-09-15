from core.domain import Offer, Signal
from core.experiments import Experiment
from core.scoring import score_offer


def _offer(**overrides):
    data = {
        "id": "o1", "name": "Test SaaS", "network": "demo",
        "url": "https://example.com/offer", "commission_rate": 0.3,
        "recurring": True, "average_order_value": 120, "cookie_days": 30,
        "payout_methods": ["bank"], "eligible_countries": ["DZ"],
        "terms_verified": True, "active": True,
    }
    data.update(overrides)
    return Offer(**data)


def test_scoring_exposes_breakdown_and_confidence():
    signal = Signal(source="rss", keyword="test", momentum=80, commercial_intent=75, competition=20)
    opp = score_offer(_offer(), signal)
    assert 0 <= opp.score <= 100
    assert 0 <= opp.confidence <= 1
    assert "momentum" in opp.breakdown
    assert opp.recommended is True


def test_ineligible_offer_is_not_recommended():
    signal = Signal(source="rss", keyword="test", momentum=90, commercial_intent=90, competition=5)
    opp = score_offer(_offer(eligible_countries=["US"]), signal, country="DZ")
    assert opp.recommended is False
    assert any("not listed as eligible" in risk for risk in opp.risks)


def test_experiment_rejects_invalid_observations_and_promotes():
    exp = Experiment("e1", min_observations=10)
    exp.record("a", clicks=10, conversions=1, revenue=2)
    exp.record("b", clicks=10, conversions=3, revenue=9)
    assert exp.ready_to_decide()
    assert exp.decision() == "b"
    assert exp.close() == "b"
    assert exp.status == "completed"


def test_experiment_rejects_conversions_above_clicks():
    exp = Experiment("e1")
    try:
        exp.record("a", clicks=1, conversions=2)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
