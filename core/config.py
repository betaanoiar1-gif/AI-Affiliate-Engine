from __future__ import annotations
import os
from dataclasses import dataclass
from .domain import RunMode


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int, minimum: int = 0) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


def _float(name: str, default: float, minimum: float = 0.0) -> float:
    try:
        return max(minimum, float(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


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
        raw_mode = os.getenv("AFFILIATE_RUN_MODE", RunMode.SIMULATION.value).strip().lower()
        try:
            mode = RunMode(raw_mode)
        except ValueError:
            mode = RunMode.SIMULATION
        country = os.getenv("DEFAULT_COUNTRY", "DZ").strip().upper() or "DZ"
        return cls(
            mode=mode,
            max_daily_publications=_int("MAX_DAILY_PUBLICATIONS", 3),
            kill_switch=_bool("KILL_SWITCH", False),
            default_country=country,
            ai_monthly_budget=_float("AI_MONTHLY_BUDGET", 0.0),
            request_timeout_seconds=_float("REQUEST_TIMEOUT_SECONDS", 15.0, 1.0),
        )


settings = Settings.from_env()
