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
    status: str = "running"
    selected_variant: str | None = None

    def record(self, variant_id: str, *, impressions: int = 0, clicks: int = 0, conversions: int = 0, revenue: float = 0.0) -> None:
        if self.status != "running":
            raise ValueError("cannot record observations on a closed experiment")
        if clicks < 0 or conversions < 0 or impressions < 0 or revenue < 0:
            raise ValueError("observations cannot be negative")
        if conversions > clicks:
            raise ValueError("conversions cannot exceed clicks")
        v = self.variants.setdefault(variant_id, Variant(variant_id))
        v.impressions += impressions
        v.clicks += clicks
        v.conversions += conversions
        v.revenue += revenue

    def _sample_score(self, v: Variant, rng: random.Random) -> float:
        # Beta posterior for conversion probability, multiplied by EPC.
        alpha = 1 + v.conversions
        beta = 1 + max(0, v.clicks - v.conversions)
        return rng.betavariate(alpha, beta) * (v.epc if v.clicks else 1.0)

    def choose(self, *, rng: random.Random | None = None) -> str:
        if not self.variants:
            raise ValueError("experiment has no variants")
        if self.status != "running":
            if self.selected_variant:
                return self.selected_variant
            raise ValueError("closed experiment has no selected variant")
        rng = rng or random.Random()
        samples = [(self._sample_score(v, rng), v.id) for v in self.variants.values()]
        return max(samples)[1]

    def ready_to_decide(self) -> bool:
        return bool(self.variants) and all(v.clicks >= self.min_observations for v in self.variants.values())

    def decision(self) -> str | None:
        """Deterministic promotion candidate once every arm has enough data."""
        if not self.ready_to_decide():
            return None
        self.selected_variant = max(self.variants.values(), key=lambda v: (v.epc, v.conversion_rate, v.revenue)).id
        return self.selected_variant

    def close(self) -> str:
        if not self.variants:
            raise ValueError("experiment has no variants")
        winner = self.decision() or self.selected_variant
        if not winner:
            raise ValueError("insufficient observations to close experiment")
        self.selected_variant = winner
        self.status = "completed"
        return winner

    def report(self) -> list[dict]:
        return [
            {"id": v.id, "impressions": v.impressions, "clicks": v.clicks, "conversions": v.conversions,
             "conversion_rate": round(v.conversion_rate, 6), "epc": round(v.epc, 6), "revenue": round(v.revenue, 2)}
            for v in sorted(self.variants.values(), key=lambda x: (x.epc, x.conversion_rate), reverse=True)
        ]
