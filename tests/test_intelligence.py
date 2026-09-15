import pytest
from core.attribution import create_click, conversion_from_click, summarize
from core.experiments import Experiment
from core.security import UnsafeURL, redact_secret, validate_public_url
from core.simulation import monte_carlo, scenario_matrix
from core.domain import Offer


def make_offer():
    return Offer(id="x", name="X", network="demo", commission_rate=20, average_order_value=100, terms_verified=True, payout_methods=["bank"])


def test_scenarios_are_ordered_and_non_negative():
    rows = scenario_matrix(make_offer(), 1000)
    assert [r["scenario"] for r in rows] == ["conservative", "base", "optimistic"]
    assert all(r["estimated_commission"] >= 0 for r in rows)


def test_monte_carlo_is_reproducible():
    a = monte_carlo(make_offer(), 500, 100, seed=42)
    b = monte_carlo(make_offer(), 500, 100, seed=42)
    assert a == b
    assert a["synthetic"] is True


def test_experiment_bandit_chooses_known_variant():
    exp = Experiment("e", min_observations=1)
    exp.record("a", clicks=100, conversions=2, revenue=20)
    exp.record("b", clicks=100, conversions=30, revenue=300)
    assert exp.choose(rng=__import__("random").Random(4)) in {"a", "b"}
    assert {r["id"] for r in exp.report()} == {"a", "b"}


def test_attribution_reconciles_unknown_conversion():
    click = create_click("offer", "campaign", "youtube", "content")
    conversion = conversion_from_click(click, 100, 20)
    assert summarize([click], [conversion])["commission"] == 20
    assert summarize([], [conversion])["conversions"] == 0


def test_public_url_security():
    assert validate_public_url("https://example.com/path").startswith("https://")
    with pytest.raises(UnsafeURL):
        validate_public_url("http://localhost:8080")
    assert redact_secret("abcdefgh") == "abcd****"
