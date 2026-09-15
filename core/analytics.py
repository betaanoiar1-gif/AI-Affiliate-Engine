from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AttributionMetric:
    clicks: int
    conversions: int
    commission: float
    ctr: float
    cvr: float
    epc: float


def aggregate_attribution(rows: Iterable[dict]) -> dict[str, AttributionMetric]:
    buckets: dict[str, dict[str, float]] = defaultdict(lambda: {"impressions": 0, "clicks": 0, "conversions": 0, "commission": 0.0})
    for row in rows:
        key = str(row.get("key") or row.get("offer_id") or "unknown")
        b = buckets[key]
        b["impressions"] += max(0, int(row.get("impressions", 0)))
        b["clicks"] += max(0, int(row.get("clicks", 0)))
        b["conversions"] += max(0, int(row.get("conversions", 0)))
        b["commission"] += max(0.0, float(row.get("commission", 0)))
    return {k: AttributionMetric(int(v["clicks"]), int(v["conversions"]), round(v["commission"], 2), round(v["clicks"] / v["impressions"], 6) if v["impressions"] else 0.0, round(v["conversions"] / v["clicks"], 6) if v["clicks"] else 0.0, round(v["commission"] / v["clicks"], 6) if v["clicks"] else 0.0) for k, v in buckets.items()}


def portfolio_summary(metrics: dict[str, AttributionMetric]) -> dict[str, float]:
    clicks = sum(x.clicks for x in metrics.values())
    conversions = sum(x.conversions for x in metrics.values())
    commission = sum(x.commission for x in metrics.values())
    return {"clicks": clicks, "conversions": conversions, "commission": round(commission, 2), "cvr": round(conversions / clicks, 6) if clicks else 0.0, "epc": round(commission / clicks, 6) if clicks else 0.0}
