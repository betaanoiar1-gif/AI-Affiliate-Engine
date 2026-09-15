from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class LearningObservation:
    opportunity_score: float
    clicks: int
    conversions: int
    revenue: float

    @property
    def realized_rate(self) -> float:
        return self.conversions / self.clicks if self.clicks else 0.0


@dataclass
class LearningEngine:
    observations: list[LearningObservation] = field(default_factory=list)

    def record(self, observation: LearningObservation) -> None:
        self.observations.append(observation)

    def calibration(self) -> dict:
        if not self.observations:
            return {"observations": 0, "mean_score": 0.0, "mean_conversion_rate": 0.0, "mean_revenue": 0.0}
        n = len(self.observations)
        return {
            "observations": n,
            "mean_score": round(sum(o.opportunity_score for o in self.observations) / n, 2),
            "mean_conversion_rate": round(sum(o.realized_rate for o in self.observations) / n, 6),
            "mean_revenue": round(sum(o.revenue for o in self.observations) / n, 2),
        }

    def score_adjustment(self, score: float, *, prior_conversion_rate: float = 0.02) -> float:
        """Conservative feedback adjustment; bounded so learning cannot destabilize ranking."""
        if not self.observations:
            return round(max(0.0, min(100.0, score)), 2)
        realized = sum(o.conversions for o in self.observations) / max(1, sum(o.clicks for o in self.observations))
        if prior_conversion_rate <= 0:
            return round(score, 2)
        ratio = max(0.5, min(1.5, realized / prior_conversion_rate))
        return round(max(0.0, min(100.0, score + (ratio - 1.0) * 10)), 2)
