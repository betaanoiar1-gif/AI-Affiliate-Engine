from __future__ import annotations
import os
from dataclasses import dataclass
from .domain import RunMode


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    mode: RunMode = RunMode.SIMULATION
    max_daily_publications: int = 3
    kill_switch: bool = False
    default_country: str = "DZ"
    ai_monthly_budget: float = 0.0
    request_timeout_seconds: float = 15.0

    @classmethod
    def from_env(cls) -> "Settings":
        raw_mode = os.getenv("AFFILIATE_RUN_MODE", RunMode.SIMULATION.value).lower()
        try:
            mode = RunMode(raw_mode)
        except ValueError:
            mode = RunMode.SIMULATION
        return cls(
            mode=mode,
            max_daily_publications=max(0, int(os.getenv("MAX_DAILY_PUBLICATIONS", "3"))),
            kill_switch=_bool("KILL_SWITCH", False),
            default_country=os.getenv("DEFAULT_COUNTRY", "DZ").upper(),
            ai_monthly_budget=max(0.0, float(os.getenv("AI_MONTHLY_BUDGET", "0"))),
            request_timeout_seconds=max(1.0, float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))),
        )


settings = Settings.from_env()
