from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


DEFAULT_BASE_URL = "https://openaffiliate.dev/api"


@dataclass(frozen=True)
class RegistryProgram:
    name: str
    slug: str
    url: str = ""
    category: str = ""
    commission_type: str = ""
    commission_rate: str = ""
    cookie_days: int | None = None
    verified: bool = False
    source: str = "openaffiliate"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RegistryProgram":
        commission = payload.get("commission") or {}
        return cls(
            name=str(payload.get("name") or payload.get("slug") or ""),
            slug=str(payload.get("slug") or ""),
            url=str(payload.get("url") or ""),
            category=str(payload.get("category") or ""),
            commission_type=str(commission.get("type") or payload.get("commission_type") or ""),
            commission_rate=str(commission.get("rate") or payload.get("commission_rate") or ""),
            cookie_days=int(payload["cookie_days"]) if payload.get("cookie_days") is not None else None,
            verified=bool(payload.get("verified", False)),
        )


class OpenAffiliateClient:
    """Optional public-registry adapter. It never becomes a hard dependency."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def search(self, query: str = "", *, category: str | None = None, verified: bool | None = None, limit: int = 20) -> list[RegistryProgram]:
        params: dict[str, Any] = {"q": query, "limit": max(1, min(100, limit))}
        if category:
            params["category"] = category
        if verified is not None:
            params["verified"] = str(verified).lower()
        response = httpx.get(f"{self.base_url}/programs", params=params, timeout=self.timeout, follow_redirects=False)
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("programs", payload) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            return []
        return [RegistryProgram.from_payload(row) for row in rows if isinstance(row, dict)]

    def get(self, slug: str) -> RegistryProgram:
        response = httpx.get(f"{self.base_url}/programs/{slug}", timeout=self.timeout, follow_redirects=False)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid OpenAffiliate response")
        return RegistryProgram.from_payload(payload)
