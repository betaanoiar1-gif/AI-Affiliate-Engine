from __future__ import annotations

from typing import Any
import httpx

from core.reliability import retry


OPENROUTER_MODELS = "https://openrouter.ai/api/v1/models"


def list_free_openrouter_models(*, limit: int = 100, timeout: float = 10.0) -> list[dict[str, Any]]:
    """Return models whose published prompt and completion pricing are both zero.

    The provider's catalog is treated as authoritative because free-model names change.
    """
    def call():
        response = httpx.get(OPENROUTER_MODELS, timeout=timeout, follow_redirects=False)
        response.raise_for_status()
        return response.json()

    payload = retry(call, attempts=2)
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    free: list[dict[str, Any]] = []
    for row in rows:
        pricing = row.get("pricing") or {}
        try:
            prompt = float(pricing.get("prompt", 1))
            completion = float(pricing.get("completion", 1))
        except (TypeError, ValueError):
            continue
        if prompt == 0 and completion == 0:
            free.append({"id": row.get("id"), "name": row.get("name"), "context_length": row.get("context_length"), "architecture": row.get("architecture")})
    return free[: max(1, min(limit, 500))]
