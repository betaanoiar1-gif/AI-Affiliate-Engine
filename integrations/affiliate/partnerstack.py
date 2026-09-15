from __future__ import annotations
import os
from core.domain import Offer
from .http_client import get_json


class PartnerStackAdapter:
    """Read-only Partner API adapter. It never performs partner-management writes."""
    base_url = "https://api.partnerstack.com/api/v2"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("PARTNERSTACK_API_KEY")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def list_partnerships(self, *, starting_after: str | None = None) -> dict:
        if not self.configured:
            return {"configured": False, "data": []}
        params = {"starting_after": starting_after} if starting_after else None
        return get_json(
            f"{self.base_url}/partnerships",
            headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
            params=params,
        )

    def normalize(self, item: dict) -> Offer:
        return Offer(
            id=f"partnerstack:{item.get('key', item.get('id', 'unknown'))}",
            name=str(item.get("name") or item.get("company_name") or "PartnerStack program"),
            network="partnerstack",
            category=str(item.get("category") or "saas"),
            url=item.get("url"),
            commission_rate=float(item.get("commission_rate") or 0),
            recurring=bool(item.get("recurring", False)),
            average_order_value=float(item.get("average_order_value") or 0),
            cookie_days=int(item.get("cookie_days") or 0),
            payout_currency=str(item.get("currency") or "USD"),
            payout_methods=list(item.get("payout_methods") or []),
            eligible_countries=list(item.get("countries") or []),
            terms_verified=False,
            active=True,
        )
