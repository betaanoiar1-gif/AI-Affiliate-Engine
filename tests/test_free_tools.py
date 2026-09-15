import os

from integrations.free_tools import catalog, fallback_chain, get_tool
from integrations.ai.router import AIRouter
from integrations.ai.model_discovery import list_free_openrouter_models


def test_catalog_contains_no_key_and_free_tier_tools():
    assert get_tool("hackernews_api").credentials is False
    assert get_tool("hackernews_api").cost == "free"
    assert "google_trends_rss" in {x.id for x in catalog(category="trend")}
    assert fallback_chain("openrouter_free")[0] == "openrouter_free"


def test_ai_router_uses_separate_provider_keys(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-or")
    monkeypatch.setenv("OPENROUTER_MODEL", "test/model")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq")
    monkeypatch.setenv("GROQ_MODEL", "test-groq-model")
    router = AIRouter()
    assert "openrouter_free:test/model" in router.available()
    assert "groq_free:test-groq-model" in router.available()


def test_free_openrouter_filter(monkeypatch):
    import integrations.ai.model_discovery as module

    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {"data": [
                {"id": "free", "name": "Free", "pricing": {"prompt": "0", "completion": "0"}},
                {"id": "paid", "name": "Paid", "pricing": {"prompt": "0.1", "completion": "0.2"}},
            ]}
    monkeypatch.setattr(module.httpx, "get", lambda *a, **k: Response())
    assert [x["id"] for x in list_free_openrouter_models()] == ["free"]
