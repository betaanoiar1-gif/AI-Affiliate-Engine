from core.domain import ContentPlan, Offer, Signal
from .interfaces import AIProvider, AnalyticsProvider, OfferProvider, Publisher, TrendProvider


class DemoOfferProvider(OfferProvider):
    def list_offers(self):
        return []


class DemoTrendProvider(TrendProvider):
    def signals(self):
        return []


class TemplateAIProvider(AIProvider):
    def create_content_plan(self, offer: Offer, signal: Signal, platform: str) -> ContentPlan:
        return ContentPlan(
            offer_id=offer.id,
            platform=platform,
            angle=f"Practical guide: {signal.keyword}",
            hook=f"3 things to know about {signal.keyword}",
            body_outline=["Problem", "Evidence", "Options", "Recommendation"],
            disclosure="This content contains affiliate links. We may earn a commission at no extra cost to you.",
            cta="Check the verified offer details.",
        )


class DryRunPublisher(Publisher):
    def publish(self, plan: ContentPlan) -> str:
        return f"dry-run:{plan.offer_id}:{plan.platform}"


class EmptyAnalytics(AnalyticsProvider):
    def metrics(self):
        return {"clicks": 0, "conversions": 0, "revenue": 0.0}
