from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import exp
from statistics import mean
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DataQuality:
    freshness: float = 1.0
    completeness: float = 1.0
    consistency: float = 1.0
    source_reliability: float = 1.0

    def score(self) -> float:
        values = [max(0.0, min(1.0, x)) for x in (self.freshness, self.completeness, self.consistency, self.source_reliability)]
        return round(mean(values) * 100, 2)


@dataclass(frozen=True)
class Provenance:
    source: str
    observed_at: datetime
    record_id: str = ""
    quality: DataQuality = field(default_factory=DataQuality)

    def as_dict(self) -> dict[str, Any]:
        return {"source": self.source, "observed_at": self.observed_at.isoformat(), "record_id": self.record_id, "quality_score": self.quality.score()}


class OfferLifecycle(str, Enum):
    DISCOVERED = "discovered"
    VERIFIED = "verified"
    ACTIVE = "active"
    TESTING = "testing"
    WINNING = "winning"
    DECLINING = "declining"
    STALE = "stale"
    SUSPENDED = "suspended"
    RETIRED = "retired"


_ALLOWED = {
    OfferLifecycle.DISCOVERED: {OfferLifecycle.VERIFIED, OfferLifecycle.SUSPENDED},
    OfferLifecycle.VERIFIED: {OfferLifecycle.ACTIVE, OfferLifecycle.SUSPENDED},
    OfferLifecycle.ACTIVE: {OfferLifecycle.TESTING, OfferLifecycle.STALE, OfferLifecycle.SUSPENDED, OfferLifecycle.RETIRED},
    OfferLifecycle.TESTING: {OfferLifecycle.WINNING, OfferLifecycle.DECLINING, OfferLifecycle.ACTIVE, OfferLifecycle.SUSPENDED},
    OfferLifecycle.WINNING: {OfferLifecycle.DECLINING, OfferLifecycle.STALE, OfferLifecycle.SUSPENDED, OfferLifecycle.RETIRED},
    OfferLifecycle.DECLINING: {OfferLifecycle.TESTING, OfferLifecycle.STALE, OfferLifecycle.RETIRED, OfferLifecycle.SUSPENDED},
    OfferLifecycle.STALE: {OfferLifecycle.ACTIVE, OfferLifecycle.RETIRED, OfferLifecycle.SUSPENDED},
    OfferLifecycle.SUSPENDED: {OfferLifecycle.VERIFIED, OfferLifecycle.ACTIVE, OfferLifecycle.RETIRED},
    OfferLifecycle.RETIRED: set(),
}


def transition_offer(current: OfferLifecycle, target: OfferLifecycle) -> OfferLifecycle:
    if target not in _ALLOWED[current]:
        raise ValueError(f"invalid offer transition: {current.value} -> {target.value}")
    return target


@dataclass(frozen=True)
class AttributionResult:
    method: str
    weights: dict[str, float]


def attribution_weights(touches: list[dict[str, Any]], method: str = "last_touch", half_life: float = 7.0) -> AttributionResult:
    if not touches:
        return AttributionResult(method, {})
    ids = [str(t.get("id", i)) for i, t in enumerate(touches)]
    n = len(ids)
    if method == "first_touch":
        raw = [1.0] + [0.0] * (n - 1)
    elif method == "last_touch":
        raw = [0.0] * (n - 1) + [1.0]
    elif method == "linear":
        raw = [1.0] * n
    elif method == "position_based":
        raw = ([0.4] if n == 1 else [0.4] + [0.2] * (n - 2) + [0.4])
    elif method == "time_decay":
        now = max((float(t.get("age_days", i)) for i, t in enumerate(touches)), default=0.0)
        raw = [exp(-max(0.0, now - float(t.get("age_days", 0))) / max(0.001, half_life)) for t in touches]
    else:
        raise ValueError("method must be first_touch, last_touch, linear, position_based, or time_decay")
    total = sum(raw)
    return AttributionResult(method, {k: round(v / total, 8) for k, v in zip(ids, raw)} if total else {})


@dataclass(frozen=True)
class Anomaly:
    metric: str
    value: float
    baseline: float
    severity: str
    reason: str


def detect_anomalies(metrics: dict[str, float], baselines: dict[str, float], ratio_threshold: float = 2.5) -> list[Anomaly]:
    out: list[Anomaly] = []
    for key, value in metrics.items():
        base = baselines.get(key)
        if base is None or base <= 0:
            continue
        ratio = value / base
        if ratio >= ratio_threshold or ratio <= 1 / ratio_threshold:
            severity = "high" if ratio >= ratio_threshold * 2 or ratio <= 1 / (ratio_threshold * 2) else "medium"
            direction = "spike" if ratio > 1 else "drop"
            out.append(Anomaly(key, value, base, severity, f"{direction}: {ratio:.2f}x baseline"))
    return out


@dataclass(frozen=True)
class Economics:
    commission: float
    refunds: float = 0.0
    chargebacks: float = 0.0
    traffic_cost: float = 0.0
    tool_cost: float = 0.0
    opportunity_cost: float = 0.0
    failure_probability: float = 0.0

    @property
    def gross_profit(self) -> float:
        return self.commission - self.refunds - self.chargebacks - self.traffic_cost - self.tool_cost - self.opportunity_cost

    @property
    def risk_adjusted_profit(self) -> float:
        return self.gross_profit * max(0.0, min(1.0, 1.0 - self.failure_probability))

    def as_dict(self) -> dict[str, float]:
        return {"gross_profit": round(self.gross_profit, 4), "risk_adjusted_profit": round(self.risk_adjusted_profit, 4)}


def market_saturation(trend_strength: float, competition: float, content_saturation: float, offer_quality: float) -> float:
    """0-100 opportunity saturation pressure; higher means more crowded."""
    score = 0.45 * competition + 0.35 * content_saturation + 0.20 * max(0.0, 100.0 - offer_quality)
    score -= 0.10 * max(0.0, min(100.0, trend_strength))
    return round(max(0.0, min(100.0, score)), 2)


def content_fatigue(recent_exposures: int, recent_engagement_rate: float, baseline_engagement_rate: float, days_since_refresh: float) -> float:
    engagement_penalty = max(0.0, 1.0 - (recent_engagement_rate / max(0.0001, baseline_engagement_rate)))
    exposure_pressure = min(1.0, recent_exposures / 100000.0)
    age_pressure = min(1.0, max(0.0, days_since_refresh) / 30.0)
    return round(max(0.0, min(100.0, 100.0 * (0.45 * engagement_penalty + 0.30 * exposure_pressure + 0.25 * age_pressure))), 2)


@dataclass
class PortfolioBucket:
    name: str
    allocation: float
    count: int = 0


def allocate_portfolio(expected_values: dict[str, float], buckets: dict[str, str], exploration_floor: float = 0.10) -> dict[str, float]:
    if not expected_values:
        return {}
    positive = {k: max(0.0, v) for k, v in expected_values.items()}
    total = sum(positive.values())
    weights = {k: (v / total if total else 1.0 / len(positive)) for k, v in positive.items()}
    floor = max(0.0, min(1.0, exploration_floor))
    exploration = [k for k, b in buckets.items() if b in {"exploration", "experimental"} and k in weights]
    if exploration and floor > 0:
        reserved = floor / len(exploration)
        for k in exploration:
            weights[k] = max(weights[k], reserved)
        s = sum(weights.values())
        weights = {k: v / s for k, v in weights.items()}
    return {k: round(v, 8) for k, v in weights.items()}


@dataclass
class KillSwitch:
    global_enabled: bool = True
    disabled_scopes: set[str] = field(default_factory=set)

    def allow(self, *scopes: str) -> bool:
        if not self.global_enabled:
            return False
        return not any(scope in self.disabled_scopes for scope in scopes)

    def disable(self, scope: str) -> None:
        self.disabled_scopes.add(scope)

    def enable(self, scope: str) -> None:
        self.disabled_scopes.discard(scope)


@dataclass(frozen=True)
class ReplayEvent:
    event_id: str
    occurred_at: datetime
    event_type: str
    snapshot: dict[str, Any]
    decision: dict[str, Any]
    outcome: dict[str, Any] = field(default_factory=dict)


def replay(events: list[ReplayEvent], until: datetime | None = None) -> list[ReplayEvent]:
    ordered = sorted(events, key=lambda e: e.occurred_at)
    return [e for e in ordered if until is None or e.occurred_at <= until]


def point_in_time_filter(rows: list[dict[str, Any]], as_of: datetime) -> list[dict[str, Any]]:
    return [r for r in rows if _parse_time(r.get("observed_at") or r.get("occurred_at")) <= as_of]


def _parse_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
