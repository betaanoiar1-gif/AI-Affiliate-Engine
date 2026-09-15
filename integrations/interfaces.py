from __future__ import annotations
from abc import ABC, abstractmethod
from core.domain import Offer, Signal, ContentPlan


class OfferProvider(ABC):
    @abstractmethod
    def list_offers(self) -> list[Offer]: ...


class TrendProvider(ABC):
    @abstractmethod
    def signals(self) -> list[Signal]: ...


class AIProvider(ABC):
    @abstractmethod
    def create_content_plan(self, offer: Offer, signal: Signal, platform: str) -> ContentPlan: ...


class Publisher(ABC):
    @abstractmethod
    def publish(self, plan: ContentPlan) -> str: ...


class AnalyticsProvider(ABC):
    @abstractmethod
    def metrics(self) -> dict: ...
