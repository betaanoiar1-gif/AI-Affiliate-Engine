from .domain import Offer, Opportunity, SimulationResult


def simulate(opportunity: Opportunity, offer: Offer, impressions: int = 10000) -> SimulationResult:
    """Deterministic scenario model; it does not claim real performance."""
    ctr = min(0.15, 0.01 + opportunity.score / 10000)
    conversion_rate = min(0.20, 0.01 + opportunity.score / 1000)
    clicks = int(impressions * ctr)
    conversions = clicks * conversion_rate
    revenue = conversions * offer.average_order_value * (offer.commission_rate / 100)
    return SimulationResult(
        opportunity_score=opportunity.score,
        estimated_clicks=clicks,
        estimated_conversions=round(conversions, 2),
        estimated_revenue=round(revenue, 2),
        assumptions={"impressions": float(impressions), "ctr": ctr, "conversion_rate": conversion_rate},
    )
