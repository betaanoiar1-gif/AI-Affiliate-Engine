from core.config import Settings


def test_malformed_environment_values_fall_back(monkeypatch):
    monkeypatch.setenv("MAX_DAILY_PUBLICATIONS", "not-a-number")
    monkeypatch.setenv("AI_MONTHLY_BUDGET", "broken")
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "0")
    settings = Settings.from_env()
    assert settings.max_daily_publications == 3
    assert settings.ai_monthly_budget == 0.0
    assert settings.request_timeout_seconds == 1.0


def test_invalid_mode_is_safe(monkeypatch):
    monkeypatch.setenv("AFFILIATE_RUN_MODE", "unknown-mode")
    assert Settings.from_env().mode.value == "simulation"
