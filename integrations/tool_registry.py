from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from integrations.free_tools import ToolSpec, catalog, get_tool


@dataclass(frozen=True)
class ToolDecision:
    task: str
    selected: str
    chain: tuple[str, ...]
    reason: str


@dataclass
class ToolHealth:
    successes: int = 0
    failures: int = 0
    cooldown_until: float = 0.0

    @property
    def available(self) -> bool:
        return monotonic() >= self.cooldown_until

    @property
    def reliability(self) -> float:
        total = self.successes + self.failures
        return 1.0 if total == 0 else self.successes / total


class ToolRegistry:
    """Chooses the cheapest viable tool first and keeps temporary provider failures local."""

    def __init__(self) -> None:
        self._health: dict[str, ToolHealth] = {}

    def health(self, tool_id: str) -> ToolHealth:
        return self._health.setdefault(tool_id, ToolHealth())

    def record_success(self, tool_id: str) -> None:
        health = self.health(tool_id)
        health.successes += 1
        health.cooldown_until = 0.0

    def record_failure(self, tool_id: str, *, cooldown_seconds: float = 30.0) -> None:
        health = self.health(tool_id)
        health.failures += 1
        health.cooldown_until = monotonic() + max(0.0, cooldown_seconds)

    def select(self, task: str, *, category: str | None = None, credentials: bool | None = None) -> ToolDecision:
        candidates = catalog(category=category)
        if credentials is not None:
            candidates = [item for item in candidates if item.credentials == credentials]
        viable = [item for item in candidates if self.health(item.id).available]
        if not viable:
            raise RuntimeError("no viable tool is currently available")

        cost_rank = {"free": 0, "free-tier": 1, "credential-required": 2, "paid-fallback": 3}
        viable.sort(key=lambda item: (cost_rank[item.cost], -self.health(item.id).reliability, 0 if item.cloud else 1, item.id))
        selected = viable[0]
        chain = (selected.id, *selected.fallback)
        return ToolDecision(
            task=task,
            selected=selected.id,
            chain=chain,
            reason=f"selected {selected.id}: cost={selected.cost}, reliability={self.health(selected.id).reliability:.2f}",
        )

    def snapshot(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for spec in catalog():
            health = self.health(spec.id)
            rows.append({
                "id": spec.id,
                "category": spec.category,
                "cost": spec.cost,
                "credentials": spec.credentials,
                "cloud": spec.cloud,
                "reliability": round(health.reliability, 4),
                "successes": health.successes,
                "failures": health.failures,
                "available": health.available,
            })
        return rows


def default_registry() -> ToolRegistry:
    return ToolRegistry()
