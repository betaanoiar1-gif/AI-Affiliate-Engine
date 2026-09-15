from __future__ import annotations
from .domain import Offer, Signal, Opportunity


WEIGHTS = {
    "momentum": 0.22,
    "intent": 0.20,
    "competition": 0.13,
    "commission": 0.12,
    "aov": 0.10,
    "recurring": 0.08,
    "cookie": 0.05,
    "terms": 0.10,
}


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, value))


def score_offer(offer: Offer, signal: Signal, country: str = "DZ") -> Opportunity:
    """Risk-aware, explainable score. Eligibility/verification can veto recommendation."""
    dimensions = {
        "momentum": _bounded(signal.momentum),
        "intent": _bounded(signal.commercial_intent),
        "competition": _bounded(100 - signal.competition),
        "commission": _bounded(offer.commission_rate * 100),
        "aov": _bounded(offer.average_order_value / 10),
        "recurring": 100.0 if offer.recurring else 0.0,
        "cookie": _bounded(offer.cookie_days / 0.6),
        "terms": 100.0 if offer.terms_verified else 0.0,
    }
    raw = sum(dimensions[k] * w for k, w in WEIGHTS.items())
    reasons: list[str] = []
    risks: list[str] = []
    if dimensions["momentum"] >= 70: reasons.append("strong trend momentum")
    if dimensions["intent"] >= 70: reasons.append("high commercial intent")
    if dimensions["competition"] >= 60: reasons.append("relatively low competition")
    if offer.recurring: reasons.append("recurring commission")
    if offer.average_order_value >= 100: reasons.append("meaningful order value")

    veto = False
    if not offer.terms_verified:
        risks.append("affiliate terms are not verified")
        raw -= 25
        veto = True
    if offer.eligible_countries and country.upper() not in {c.upper() for c in offer.eligible_countries}:
        risks.append(f"country {country} is not listed as eligible")
        raw -= 50
        veto = True
    if not offer.payout_methods:
        risks.append("payout method is unknown")
        raw -= 8
    if not offer.active:
        risks.append("offer is inactive")
        raw -= 60
        veto = True
    score = round(_bounded(raw), 2)
    return Opportunity(offer_id=offer.id, score=score, reasons=reasons, risks=risks, recommended=score >= 65 and not veto)
