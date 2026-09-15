from datetime import datetime, timezone, timedelta

import pytest

from core.decision_intelligence import (
    DataQuality, Economics, OfferLifecycle, allocate_portfolio,
    attribution_weights, content_fatigue, detect_anomalies,
    market_saturation, transition_offer,
)


def test_quality_score_and_economics():
    assert DataQuality(.8, .9, 1, .7).score() == 85.0
    result = Economics(100, refunds=10, chargebacks=5, traffic_cost=20, tool_cost=5, failure_probability=.2)
    assert result.gross_profit == 60
    assert result.risk_adjusted_profit == 48


def test_multi_touch_methods_normalize():
    touches = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    for method in ("first_touch", "last_touch", "linear", "position_based", "time_decay"):
        weights = attribution_weights(touches, method).weights
        assert abs(sum(weights.values()) - 1.0) < 1e-8


def test_lifecycle_rejects_invalid_transition():
    assert transition_offer(OfferLifecycle.DISCOVERED, OfferLifecycle.VERIFIED) is OfferLifecycle.VERIFIED
    with pytest.raises(ValueError):
        transition_offer(OfferLifecycle.RETIRED, OfferLifecycle.ACTIVE)


def test_anomaly_detection_is_conservative():
    found = detect_anomalies({"clicks": 1000, "ctr": .01}, {"clicks": 100, "ctr": .01})
    assert [x.metric for x in found] == ["clicks"]


def test_saturation_and_fatigue_are_bounded():
    assert 0 <= market_saturation(100, 100, 100, 0) <= 100
    assert 0 <= content_fatigue(100000, .001, .02, 30) <= 100


def test_portfolio_keeps_exploration():
    weights = allocate_portfolio({"winner": 100, "experiment": 0}, {"winner": "proven", "experiment": "experimental"}, .10)
    assert abs(sum(weights.values()) - 1) < 1e-8
    assert weights["experiment"] >= .09
