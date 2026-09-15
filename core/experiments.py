from __future__ import annotations
from dataclasses import dataclass, field
import math
import random


@dataclass
class Variant:
    id: str
    impressions: int = 0
    conversions: int = 0
    clicks: int = 0
    revenue: float = 0.0

    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.clicks if self.clicks else 0.0

    @property
    def epc(self) -> float:
        return self.revenue / self.clicks if self.clicks else 0.0


@dataclass
class Experiment:
    id: str
    variants: dict[str, Variant] = field(default_factory=dict)
    min_observations: int = 100

    def record(self, variant_id: str, *, impressions: int = 0, clicks: int = 0, conversions: int = 0, revenue: float = 0.0) -> None:
        v = self.variants.setdefault(variant_id, Variant(variant_id))
        v.impressions += max(0, impressions)
        v.clicks += max(0, clicks)
        v.conversions += max(0, conversions)
        v.revenue += max(0.0, revenue)

    def choose(self, *, rng: random.Random | None = None) -> str:
        if not self.variants:
            raise ValueError("experiment has no variants")
        rng = rng or random.Random()
        eligible = [v for v in self.variants.values() if v.clicks >= self.min_observations]
        pool = eligible or list(self.variants.values())
        samples: list[tuple[float, str]] = []
        for v in pool:
            alpha = 1 + v.conversions
            beta = 1 + max(0, v.clicks - v.conversions)
            samples.append((rng.betavariate(alpha, beta), v.id))
        return max(samples)[1]

    def report(self) -> list[dict]:
        return [
            {"id": v.id, "impressions": v.impressions, "clicks": v.clicks, "conversions": v.conversions,
             "conversion_rate": round(v.conversion_rate, 6), "epc": round(v.epc, 6), "revenue": round(v.revenue, 2)}
            for v in sorted(self.variants.values(), key=lambda x: x.epc, reverse=True)
        ]
