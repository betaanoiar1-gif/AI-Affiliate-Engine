from .domain import Offer, Signal, Opportunity


def score_offer(offer: Offer, signal: Signal, country: str = "DZ") -> Opportunity:
    score = 0.0
    reasons: list[str] = []
    risks: list[str] = []

    score += signal.momentum * 0.25
    score += signal.commercial_intent * 0.20
    score += (100 - signal.competition) * 0.15
    score += min(offer.commission_rate * 100, 25) * 0.12
    score += min(offer.average_order_value / 20, 100) * 0.10
    score += 10 if offer.recurring else 0
    score += min(offer.cookie_days, 60) / 6 * 0.03
    score += 5 if offer.terms_verified else 0

    if signal.momentum >= 70: reasons.append("strong momentum")
    if signal.commercial_intent >= 70: reasons.append("high commercial intent")
    if signal.competition <= 40: reasons.append("manageable competition")
    if offer.recurring: reasons.append("recurring commission potential")

    if not offer.terms_verified:
        risks.append("affiliate terms are not verified")
        score -= 15
    if offer.eligible_countries and country not in offer.eligible_countries:
        risks.append(f"country {country} is not listed as eligible")
        score -= 40
    if not offer.payout_methods:
        risks.append("payout method is unknown")
        score -= 10
    if not offer.active:
        risks.append("offer is inactive")
        score -= 50

    score = max(0, min(100, round(score, 2)))
    recommended = score >= 65 and not any("not" in r or "unknown" in r for r in risks)
    return Opportunity(offer_id=offer.id, score=score, reasons=reasons, risks=risks, recommended=recommended)
