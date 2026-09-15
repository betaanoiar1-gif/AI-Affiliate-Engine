from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import sqrt
from typing import Iterable

from .domain import Offer, Signal


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class TrendObservation:
    source: str
    keyword: str
    velocity: float = 0.0
    persistence: float = 0.0
    intent: float = 0.0
    novelty: float = 0.0
    saturation: float = 0.0
    seasonality: float = 0.0
    captured_at: datetime = field(default_factory=utcnow)

    def normalized(self) -> "TrendObservation":
        clamp = lambda x: max(0.0, min(100.0, float(x)))
        return TrendObservation(self.source, self.keyword.strip(), clamp(self.velocity), clamp(self.persistence),
                                clamp(self.intent), clamp(self.novelty), clamp(self.saturation), clamp(self.seasonality), self.captured_at)

    @property
    def momentum(self) -> float:
        # Velocity is deliberately tempered by persistence so short-lived spikes do not dominate.
        t = self.normalized()
        return round(0.42 * t.velocity + 0.28 * t.persistence + 0.18 * t.novelty + 0.12 * t.seasonality, 2)


@dataclass(frozen=True)
class OpportunityAssessment:
    offer_id: str
    keyword: str
    value: float
    confidence: float
    expected_commission_per_click: float
    reasons: tuple[str, ...]
    risks: tuple[str, ...]
    evidence: dict[str, float]


def assess_opportunity(offer: Offer, trend: TrendObservation, country: str = "DZ") -> OpportunityAssessment:
    t = trend.normalized()
    country_ok = not offer.eligible_countries or country.upper() in {c.upper() for c in offer.eligible_countries}
    payout_known = bool(offer.payout_methods)
    metadata = [offer.terms_verified, payout_known, bool(offer.url), bool(offer.eligible_countries)]
    confidence = round(sum(metadata) / len(metadata), 2)

    # This is a prioritization value, not a promise of revenue.
    offer_quality = min(100.0, offer.commission_rate * 100.0) * 0.30
    offer_quality += min(100.0, offer.average_order_value / 10.0) * 0.20
    offer_quality += 100.0 if offer.recurring else 0.0
    offer_quality *= 0.5
    market = t.momentum * 0.38 + t.intent * 0.30 + (100.0 - t.saturation) * 0.20 + t.persistence * 0.12
    value = 0.62 * market + 0.38 * offer_quality

    risks: list[str] = []
    reasons: list[str] = []
    if not offer.terms_verified:
        risks.append("terms_unverified")
    if not payout_known:
        risks.append("payout_method_unknown")
    if not country_ok:
        risks.append("country_not_eligible")
    if not offer.active:
        risks.append("offer_inactive")
    if t.saturation >= 75:
        risks.append("high_market_saturation")
    if t.persistence < 25 and t.velocity >= 75:
        risks.append("possible_short_lived_spike")
    if t.intent >= 70:
        reasons.append("high_commercial_intent")
    if t.momentum >= 70:
        reasons.append("strong_trend_momentum")
    if t.novelty >= 65:
        reasons.append("novel_topic")
    if offer.recurring:
        reasons.append("recurring_commission")
    if country_ok:
        reasons.append("country_compatible_or_unrestricted")

    # Hard constraints reduce priority to zero rather than hiding policy failures.
    if not country_ok or not offer.active or not offer.terms_verified:
        value *= 0.15
    expected_epc = max(0.0, offer.average_order_value * offer.commission_rate / 100.0) * 0.02
    return OpportunityAssessment(offer.id, t.keyword, round(max(0.0, min(100.0, value)), 2), confidence,
                                 round(expected_epc, 4), tuple(reasons), tuple(risks),
                                 {"momentum": t.momentum, "intent": t.intent, "saturation": t.saturation,
                                  "persistence": t.persistence, "offer_quality": round(offer_quality, 2)})


def deduplicate_trends(observations: Iterable[TrendObservation]) -> list[TrendObservation]:
    """Merge duplicate keywords across sources without pretending sources are independent samples."""
    groups: dict[str, list[TrendObservation]] = {}
    for item in observations:
        n = item.normalized()
        if n.keyword:
            groups.setdefault(n.keyword.casefold(), []).append(n)
    merged: list[TrendObservation] = []
    for items in groups.values():
        total = float(len(items))
        avg = lambda attr: sum(getattr(x, attr) for x in items) / total
        merged.append(TrendObservation("multi_source", items[0].keyword, avg("velocity"), avg("persistence"),
                                       avg("intent"), avg("novelty"), avg("saturation"), avg("seasonality")))
    return sorted(merged, key=lambda x: x.momentum, reverse=True)
