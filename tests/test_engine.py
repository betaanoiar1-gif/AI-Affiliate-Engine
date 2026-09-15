from fastapi.testclient import TestClient
from apps.api.main import app
from core.domain import Offer, Signal
from core.scoring import score_offer
from core.policies import PolicyEngine


def offer(**kw):
    base = dict(id="demo", name="Demo", network="demo", commission_rate=0.2, recurring=True, average_order_value=100, cookie_days=30, eligible_countries=["DZ"], terms_verified=True, payout_methods=["bank"])
    base.update(kw)
    return Offer(**base)


def test_score_is_bounded_and_recommends_verified_offer():
    result = score_offer(offer(), Signal(source="test", keyword="ai", momentum=90, commercial_intent=90, competition=20))
    assert 0 <= result.score <= 100
    assert result.recommended is True


def test_unverified_offer_is_not_recommended():
    result = score_offer(offer(terms_verified=False), Signal(source="test", keyword="ai", momentum=90, commercial_intent=90, competition=20))
    assert result.recommended is False
    assert result.score < 65


def test_simulation_endpoint():
    client = TestClient(app)
    response = client.post("/api/v1/simulations", json={"opportunity_score":80,"offer":offer().model_dump(mode="json"),"impressions":10000})
    assert response.status_code == 200
    data = response.json()
    assert data["estimated_clicks"] >= 0
    assert data["estimated_revenue"] >= 0


def test_simulation_mode_blocks_publishing():
    allowed, reason = PolicyEngine().can_publish(terms_verified=True, disclosure_present=True, daily_count=0)
    assert allowed is False
    assert "simulation" in reason
