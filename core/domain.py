from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RunMode(str, Enum):
    SIMULATION = "simulation"
    APPROVAL = "approval"
    AUTONOMOUS = "autonomous"


class Offer(BaseModel):
    id: str
    name: str
    network: str
    category: str = "general"
    url: HttpUrl | None = None
    commission_rate: float = Field(default=0, ge=0)
    recurring: bool = False
    average_order_value: float = Field(default=0, ge=0)
    cookie_days: int = Field(default=0, ge=0)
    payout_currency: str = "USD"
    payout_methods: list[str] = Field(default_factory=list)
    eligible_countries: list[str] = Field(default_factory=list)
    terms_verified: bool = False
    active: bool = True


class Signal(BaseModel):
    source: str
    keyword: str
    momentum: float = Field(ge=0, le=100)
    commercial_intent: float = Field(ge=0, le=100)
    competition: float = Field(ge=0, le=100)
    captured_at: datetime = Field(default_factory=utcnow)


class Opportunity(BaseModel):
    offer_id: str
    score: float = Field(ge=0, le=100)
    reasons: list[str]
    risks: list[str]
    recommended: bool
    confidence: float = Field(default=0.0, ge=0, le=1)
    breakdown: dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class ContentPlan(BaseModel):
    offer_id: str
    platform: str
    angle: str
    hook: str
    body_outline: list[str]
    disclosure: str
    cta: str
    status: str = "planned"


class SimulationResult(BaseModel):
    opportunity_score: float
    estimated_clicks: int = Field(ge=0)
    estimated_conversions: float = Field(ge=0)
    estimated_revenue: float = Field(ge=0)
    assumptions: dict[str, float]
    simulated_at: datetime = Field(default_factory=utcnow)
