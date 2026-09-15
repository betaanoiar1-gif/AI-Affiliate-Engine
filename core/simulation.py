from __future__ import annotations
from dataclasses import dataclass
import math
import random
from .domain import Offer, Opportunity, SimulationResult


@dataclass(frozen=True)
class Scenario:
    name: str
    ctr: float
    conversion_rate: float


SCENARIOS = (
    Scenario("conservative", 0.008, 0.012),
    Scenario("base", 0.018, 0.025),
    Scenario("optimistic", 0.035, 0.045),
)


def simulate(opportunity: Opportunity, offer: Offer, impressions: int = 10000) -> SimulationResult:
    """Deterministic baseline retained for API compatibility; never presented as a forecast guarantee."""
    if impressions < 0:
        raise ValueError("impressions must be non-negative")
    ctr = min(0.15, 0.006 + opportunity.score / 12000)
    conversion_rate = min(0.20, 0.008 + opportunity.score / 1200)
    clicks = int(impressions * ctr)
    conversions = clicks * conversion_rate
    revenue = conversions * offer.average_order_value * (offer.commission_rate / 100)
    return SimulationResult(opportunity_score=opportunity.score, estimated_clicks=clicks,
        estimated_conversions=round(conversions, 2), estimated_revenue=round(revenue, 2),
        assumptions={"impressions": float(impressions), "ctr": ctr, "conversion_rate": conversion_rate})


def scenario_matrix(offer: Offer, impressions: int = 10000) -> list[dict]:
    if impressions < 0:
        raise ValueError("impressions must be non-negative")
    result = []
    for s in SCENARIOS:
        clicks = impressions * s.ctr
        conversions = clicks * s.conversion_rate
        commission = conversions * offer.average_order_value * offer.commission_rate / 100
        result.append({"scenario": s.name, "impressions": impressions, "ctr": s.ctr,
                       "clicks": round(clicks, 2), "conversion_rate": s.conversion_rate,
                       "conversions": round(conversions, 2), "estimated_commission": round(commission, 2)})
    return result


def monte_carlo(offer: Offer, impressions: int = 10000, runs: int = 2000, seed: int = 7) -> dict:
    """Synthetic uncertainty lab. It is explicitly not real-world performance data."""
    if impressions < 0 or runs < 1:
        raise ValueError("invalid simulation parameters")
    rng = random.Random(seed)
    values = []
    for _ in range(runs):
        ctr = max(0.0, min(0.15, rng.betavariate(3, 120)))
        cvr = max(0.0, min(0.20, rng.betavariate(2, 70)))
        clicks = rng.binomialvariate(impressions, ctr) if hasattr(rng, "binomialvariate") else sum(rng.random() < ctr for _ in range(impressions))
        conversions = rng.binomialvariate(clicks, cvr) if hasattr(rng, "binomialvariate") else sum(rng.random() < cvr for _ in range(clicks))
        values.append(conversions * offer.average_order_value * offer.commission_rate / 100)
    values.sort()
    mean = sum(values) / runs
    return {"runs": runs, "seed": seed, "mean_commission": round(mean, 2),
            "p10": round(values[max(0, int(runs * .10) - 1)], 2),
            "median": round(values[int(runs * .50) - 1], 2),
            "p90": round(values[int(runs * .90) - 1], 2),
            "synthetic": True}
