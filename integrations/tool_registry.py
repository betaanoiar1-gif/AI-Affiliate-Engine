from __future__ import annotations

import os
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


# A credential-required tool is only viable when its expected credential exists.
# Keep this mapping explicit so selection never silently chooses an unusable adapter.
CREDENTIAL_ENV: dict[str, tuple[str, ...]] = {
    "awin": ("AWIN_API_KEY", "AWIN_TOKEN"),
    "partnerstack": ("PARTNERSTACK_API_KEY", "PARTNERSTACK_TOKEN"),
    "youtube_data_api": ("YOUTUBE_API_KEY", "YOUTUBE_DATA_API_KEY"),
    "openrouter_free": ("OPENROUTER_API_KEY",),
    "gemini_free": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "groq_free": ("GROQ_API_KEY",),
    "huggingface_free": ("HUGGINGFACE_API_KEY", "HF_TOKEN"),
}


def has_credentials(tool_id: str) -> bool:
    names = CREDENTIAL_ENV.get(tool_id, ())
    return bool(names) and any(bool(os.getenv(name, "").strip()) for name in names)


class ToolRegistry:
    """Chooses the cheapest *configured* viable tool and isolates temporary failures."""

    def __init__(self) -> None:
        self._health: dict[str, ToolHealth] = {}

    def _validate(self, tool_id: str) -> ToolSpec:
        return get_tool(tool_id)

    def health(self, tool_id: str) -> ToolHealth:
        self._validate(tool_id)
        return self._health.setdefault(tool_id, ToolHealth())

    def record_success(self, tool_id: str) -> None:
        health = self.health(tool_id)
        health.successes += 1
        health.cooldown_until = 0.0

    def record_failure(self, tool_id: str, *, cooldown_seconds: float = 30.0) -> None:
        health = self.health(tool_id)
        health.failures += 1
        health.cooldown_until = monotonic() + max(0.0, cooldown_seconds)

    def _configured(self, spec: ToolSpec) -> bool:
        return not spec.credentials or has_credentials(spec.id)

    def select(self, task: str, *, category: str | None = None, credentials: bool | None = None) -> ToolDecision:
        candidates = catalog(category=category)
        if credentials is not None:
            candidates = [item for item in candidates if item.credentials == credentials]
        viable = [item for item in candidates if self.health(item.id).available and self._configured(item)]
        if not viable:
            raise RuntimeError("no configured and viable tool is currently available")

        cost_rank = {"free": 0, "free-tier": 1, "credential-required": 2, "paid-fallback": 3}
        viable.sort(key=lambda item: (cost_rank[item.cost], -self.health(item.id).reliability, 0 if item.cloud else 1, item.id))
        selected = viable[0]
        chain = tuple(tool_id for tool_id in (selected.id, *selected.fallback) if self._configured(get_tool(tool_id)))
        return ToolDecision(
            task=task,
            selected=selected.id,
            chain=chain or (selected.id,),
            reason=f"selected {selected.id}: cost={selected.cost}, reliability={self.health(selected.id).reliability:.2f}, configured=true",
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
                "configured": self._configured(spec),
                "cloud": spec.cloud,
                "reliability": round(health.reliability, 4),
                "successes": health.successes,
                "failures": health.failures,
                "available": health.available and self._configured(spec),
            })
        return rows


def default_registry() -> ToolRegistry:
    return ToolRegistry()
