from __future__ import annotations
from typing import Any
import httpx
from core.reliability import retry
from core.security import validate_public_url


class ProviderHTTPError(RuntimeError):
    pass


def get_json(url: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None, timeout: float = 15.0) -> dict[str, Any]:
    safe = validate_public_url(url)
    def call() -> dict[str, Any]:
        response = httpx.get(safe, headers=headers, params=params, timeout=timeout, follow_redirects=False)
        if response.status_code == 429 or response.status_code >= 500:
            raise ProviderHTTPError(f"provider temporary failure: {response.status_code}")
        if response.status_code >= 400:
            raise ProviderHTTPError(f"provider rejected request: {response.status_code}")
        data = response.json()
        if not isinstance(data, dict):
            raise ProviderHTTPError("provider response must be a JSON object")
        return data
    return retry(call, attempts=3)
