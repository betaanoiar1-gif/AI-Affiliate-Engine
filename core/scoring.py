from __future__ import annotations
from .domain import Offer, Signal, Opportunity

# Weights sum to 1.0. Revenue potential matters, but trust/terms and market fit
# prevent a high commission from dominating the decision.
WEIGHTS = {
    "momentum": 0.20,
    "intent": 0.18,
    "competition": 0.12,
    "commission": 0.12,
    "aov": 0.10,
    "recurring": 0.08,
    "cookie": 0.05,
    "terms": 0.10,
    "payout": 0.05,
}


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _log_scale(value: float, scale: float) -> float:
    # Avoid treating a $2,000 AOV as 20x better than $100.
    import math
    if value <= 0:
        return 0.0
    return _bounded(100.0 * math.log1p(value) / math.log1p(scale))


def _country_ok(offer: Offer, country: str) -> bool:
    return not offer.eligible_countries or country.upper() in {c.upper() for c in offer.eligible_countries}


def score_offer(offer: Offer, signal: Signal, country: str = "DZ") -> Opportunity:
    """Return an explainable, risk-adjusted 0-100 opportunity score.

    Hard policy constraints veto recommendation; soft risks reduce the score.
    The confidence value expresses how much of the decision is supported by
    verified offer metadata rather than pretending to be a probability of sale.
    """
    dimensions = {
        "momentum": _bounded(signal.momentum),
        "intent": _bounded(signal.commercial_intent),
        "competition": _bounded(100 - signal.competition),
        "commission": _bounded(offer.commission_rate * 100),
        "aov": _log_scale(offer.average_order_value, 1000),
        "recurring": 100.0 if offer.recurring else 0.0,
        "cookie": _bounded(offer.cookie_days / 0.6),
        "terms": 100.0 if offer.terms_verified else 0.0,
        "payout": 100.0 if offer.payout_methods else 35.0,
    }
    raw = sum(dimensions[k] * w for k, w in WEIGHTS.items())
    reasons: list[str] = []
    risks: list[str] = []
    veto = False

    if dimensions["momentum"] >= 70: reasons.append("strong trend momentum")
    if dimensions["intent"] >= 70: reasons.append("high commercial intent")
    if dimensions["competition"] >= 60: reasons.append("relatively favorable competition")
    if offer.recurring: reasons.append("recurring commission")
    if offer.average_order_value >= 100: reasons.append("meaningful order value")
    if offer.payout_methods: reasons.append("payout method documented")

    if not offer.terms_verified:
        risks.append("affiliate terms are not verified")
        raw -= 30
        veto = True
    if not _country_ok(offer, country):
        risks.append(f"country {country} is not listed as eligible")
        raw -= 50
        veto = True
    if not offer.payout_methods:
        risks.append("payout method is unknown")
        raw -= 10
    if not offer.active:
        risks.append("offer is inactive")
        raw -= 60
        veto = True

    # Confidence is metadata completeness, not a prediction of conversion.
    evidence = [offer.terms_verified, bool(offer.payout_methods), bool(offer.eligible_countries), bool(offer.url)]
    confidence = round(sum(evidence) / len(evidence), 2)
    score = round(_bounded(raw), 2)
    return Opportunity(
        offer_id=offer.id,
        score=score,
        reasons=reasons,
        risks=risks,
        recommended=score >= 65 and confidence >= 0.5 and not veto,
        confidence=confidence,
        breakdown={k: round(v, 2) for k, v in dimensions.items()},
    )
