from __future__ import annotations
import os
from core.domain import Offer
from .http_client import get_json


class AwinPublisherAdapter:
    """Read-only Awin publisher adapter. Credentials and publisher id stay outside source control."""
    base_url = "https://api.awin.com"

    def __init__(self, token: str | None = None, publisher_id: int | None = None):
        self.token = token or os.getenv("AWIN_API_TOKEN")
        raw_id = publisher_id if publisher_id is not None else os.getenv("AWIN_PUBLISHER_ID")
        self.publisher_id = int(raw_id) if raw_id else None

    @property
    def configured(self) -> bool:
        return bool(self.token and self.publisher_id)

    def list_promotions(self, *, page: int = 1, page_size: int = 50) -> dict:
        if not self.configured:
            return {"configured": False, "items": []}
        return get_json(
            f"{self.base_url}/publishers/{self.publisher_id}/promotions",
            headers={"Authorization": f"Bearer {self.token}"},
            params={"page": page, "pageSize": page_size},
        )

    def normalize(self, item: dict) -> Offer:
        commission = item.get("commission", 0) or 0
        if isinstance(commission, dict):
            commission = commission.get("amount", commission.get("rate", 0))
        return Offer(
            id=f"awin:{item.get('id', item.get('advertiserId', 'unknown'))}",
            name=str(item.get("title") or item.get("advertiserName") or "Awin offer"),
            network="awin",
            category=str(item.get("category") or "general"),
            url=item.get("url"),
            commission_rate=float(commission or 0),
            recurring=bool(item.get("recurring", False)),
            average_order_value=float(item.get("averageOrderValue") or 0),
            cookie_days=int(item.get("cookieDays") or 0),
            payout_currency=str(item.get("currency") or "USD"),
            payout_methods=list(item.get("payoutMethods") or []),
            eligible_countries=list(item.get("regions") or item.get("countries") or []),
            terms_verified=False,
            active=True,
        )
