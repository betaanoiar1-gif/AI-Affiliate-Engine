from __future__ import annotations
from dataclasses import dataclass
from .domain import Offer, Signal, Opportunity, SimulationResult, ContentPlan, RunMode
from .scoring import score_offer
from .simulation import simulate
from integrations.interfaces import AIProvider, Publisher
from .compliance import ComplianceEngine
from .content import validate_content


@dataclass
class CycleResult:
    opportunity: Opportunity
    simulation: SimulationResult
    content: ContentPlan | None
    publication_id: str | None
    blocked_reason: str | None


class AutonomousEngine:
    """Side-effect-aware discover-to-learn orchestration.

    Simulation never publishes. Approval mode prepares a publication candidate
    but stops before the external side effect. Autonomous mode can publish only
    after all compliance and content gates pass.
    """
    def __init__(self, ai: AIProvider | None = None, publisher: Publisher | None = None, compliance: ComplianceEngine | None = None):
        self.ai = ai
        self.publisher = publisher
        self.compliance = compliance or ComplianceEngine()

    def evaluate(self, offer: Offer, signal: Signal, country: str = "DZ", platform: str = "youtube") -> CycleResult:
        opportunity = score_offer(offer, signal, country)
        simulation = simulate(opportunity, offer)
        if not opportunity.recommended:
            return CycleResult(opportunity, simulation, None, None, "opportunity failed score/risk gate")
        if self.ai is None:
            return CycleResult(opportunity, simulation, None, None, "AI content adapter not configured")

        content = self.ai.create_content_plan(offer, signal, platform)
        check = validate_content(content)
        if not check.allowed:
            return CycleResult(opportunity, simulation, content, None, "; ".join(check.reasons))

        decision = self.compliance.check_publish(offer, content, daily_count=0)
        if not decision.allowed:
            return CycleResult(opportunity, simulation, content, None, "; ".join(decision.reasons))
        if self.compliance.mode != RunMode.AUTONOMOUS:
            return CycleResult(opportunity, simulation, content, None, "approval required before external publishing")
        if self.publisher is None:
            return CycleResult(opportunity, simulation, content, None, "publisher adapter not configured")

        publication_id = self.publisher.publish(content)
        return CycleResult(opportunity, simulation, content, publication_id, None)
