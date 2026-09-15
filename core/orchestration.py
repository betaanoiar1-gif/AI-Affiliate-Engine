from __future__ import annotations
from dataclasses import dataclass
from .domain import Offer, Signal, Opportunity, SimulationResult, ContentPlan
from .scoring import score_offer
from .simulation import simulate
from integrations.interfaces import AIProvider, Publisher
from .compliance import ComplianceEngine


@dataclass
class CycleResult:
    opportunity: Opportunity
    simulation: SimulationResult
    content: ContentPlan | None
    publication_id: str | None
    blocked_reason: str | None


class AutonomousEngine:
    """Side-effect-aware discover-to-learn orchestration. External effects stay policy gated."""
    def __init__(self, ai: AIProvider | None = None, publisher: Publisher | None = None, compliance: ComplianceEngine | None = None):
        self.ai = ai
        self.publisher = publisher
        self.compliance = compliance or ComplianceEngine()

    def evaluate(self, offer: Offer, signal: Signal, country: str = "DZ", platform: str = "youtube") -> CycleResult:
        opportunity = score_offer(offer, signal, country)
        simulation = simulate(opportunity, offer)
        content = self.ai.create_content_plan(offer, signal, platform) if self.ai and opportunity.recommended else None
        if content is None or self.publisher is None:
            return CycleResult(opportunity, simulation, content, None, "content or publisher adapter not configured")
        decision = self.compliance.check_publish(offer, content, daily_count=0)
        if not decision.allowed:
            return CycleResult(opportunity, simulation, content, None, "; ".join(decision.reasons))
        publication_id = self.publisher.publish(content)
        return CycleResult(opportunity, simulation, content, publication_id, None)
