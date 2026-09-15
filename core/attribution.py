from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Click:
    id: str
    offer_id: str
    campaign_id: str
    platform: str
    content_id: str
    occurred_at: datetime


@dataclass(frozen=True)
class Conversion:
    id: str
    click_id: str
    order_value: float
    commission: float
    currency: str
    occurred_at: datetime


def create_click(offer_id: str, campaign_id: str, platform: str, content_id: str) -> Click:
    return Click(str(uuid4()), offer_id, campaign_id, platform, content_id, utcnow())


def conversion_from_click(click: Click, order_value: float, commission_rate: float, currency: str = "USD") -> Conversion:
    if order_value < 0 or commission_rate < 0:
        raise ValueError("financial values cannot be negative")
    return Conversion(str(uuid4()), click.id, order_value, order_value * commission_rate / 100, currency, utcnow())


def summarize(clicks: list[Click], conversions: list[Conversion]) -> dict:
    click_ids = {c.id for c in clicks}
    valid = [c for c in conversions if c.click_id in click_ids]
    revenue = sum(c.commission for c in valid)
    return {"clicks": len(clicks), "conversions": len(valid), "commission": round(revenue, 2),
            "conversion_rate": round(len(valid) / len(clicks), 6) if clicks else 0.0,
            "epc": round(revenue / len(clicks), 6) if clicks else 0.0}
