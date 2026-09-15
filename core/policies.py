from .domain import RunMode


class PolicyEngine:
    """Central guardrail layer. Publishing is opt-in and simulation is the default."""

    def __init__(self, mode: RunMode = RunMode.SIMULATION, max_daily_publications: int = 3):
        self.mode = mode
        self.max_daily_publications = max_daily_publications

    def can_publish(self, *, terms_verified: bool, disclosure_present: bool, daily_count: int) -> tuple[bool, str]:
        if self.mode == RunMode.SIMULATION:
            return False, "simulation mode blocks publishing"
        if not terms_verified:
            return False, "affiliate terms must be verified"
        if not disclosure_present:
            return False, "affiliate disclosure is required"
        if daily_count >= self.max_daily_publications:
            return False, "daily publication limit reached"
        return True, "allowed"
