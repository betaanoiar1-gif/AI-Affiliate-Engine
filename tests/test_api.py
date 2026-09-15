from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_health_contract():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "mode" in body
    assert "kill_switch" in body
    assert "version" in body


def test_capabilities_contract():
    response = client.get("/api/v1/capabilities")
    assert response.status_code == 200
    modules = response.json()["modules"]
    assert "scoring" in modules
    assert "simulation" in modules
    assert "learning" in modules


def test_security_endpoint_rejects_non_https():
    response = client.post("/api/v1/security/validate-url", json={"url": "http://example.com"})
    assert response.status_code == 400


def test_score_endpoint():
    payload = {
        "offer": {
            "id": "o1", "name": "Test", "network": "demo",
            "url": "https://example.com", "commission_rate": 0.2,
            "payout_methods": ["bank"], "eligible_countries": ["DZ"],
            "terms_verified": True, "active": True
        },
        "signal": {
            "source": "test", "keyword": "x", "momentum": 80,
            "commercial_intent": 70, "competition": 20
        },
        "country": "DZ"
    }
    response = client.post("/api/v1/opportunities/score", json=payload)
    assert response.status_code == 200
    assert 0 <= response.json()["score"] <= 100
