from __future__ import annotations
from dataclasses import dataclass
from .domain import ContentPlan, Offer, RunMode


@dataclass(frozen=True)
class ComplianceDecision:
    allowed: bool
    reasons: tuple[str, ...]


class ComplianceEngine:
    def __init__(self, mode: RunMode = RunMode.SIMULATION, kill_switch: bool = False, max_daily_publications: int = 3):
        self.mode = mode
        self.kill_switch = kill_switch
        self.max_daily_publications = max_daily_publications

    def check_publish(self, offer: Offer, plan: ContentPlan, daily_count: int) -> ComplianceDecision:
        reasons: list[str] = []
        if self.kill_switch:
            reasons.append("global kill switch is active")
        if self.mode == RunMode.SIMULATION:
            reasons.append("simulation mode blocks external publishing")
        if not offer.active:
            reasons.append("offer is inactive")
        if not offer.terms_verified:
            reasons.append("affiliate terms are not verified")
        if not plan.disclosure.strip():
            reasons.append("affiliate disclosure is required")
        if daily_count >= self.max_daily_publications:
            reasons.append("daily publication limit reached")
        if plan.offer_id != offer.id:
            reasons.append("content plan does not match offer")
        return ComplianceDecision(not reasons, tuple(reasons))
