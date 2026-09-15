from integrations.tool_registry import ToolRegistry


def test_registry_prefers_no_payment_tool_for_web():
    registry = ToolRegistry()
    decision = registry.select("fetch a public page", category="web")
    assert decision.selected in {"httpx", "beautifulsoup4", "trafilatura"}
    assert decision.chain[0] == decision.selected


def test_registry_cooldown_and_recovery():
    registry = ToolRegistry()
    registry.record_failure("httpx", cooldown_seconds=60)
    assert not registry.health("httpx").available
    registry.record_success("httpx")
    assert registry.health("httpx").available
    assert registry.health("httpx").successes == 1


def test_catalog_separates_ai_from_other_tools():
    from integrations.free_tools import catalog
    assert catalog(exclude_ai=True)
    assert all(item.category != "ai" for item in catalog(exclude_ai=True))
    assert all(item.cost == "free" for item in catalog(only_no_payment=True))
