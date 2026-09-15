from integrations.affiliate.awin import AwinPublisherAdapter
from integrations.affiliate.partnerstack import PartnerStackAdapter
from integrations.ai.router import AIRouter, AIModel


def test_affiliate_adapters_are_safe_without_credentials():
    assert AwinPublisherAdapter().configured is False
    assert AwinPublisherAdapter().list_promotions()["configured"] is False
    assert PartnerStackAdapter().configured is False
    assert PartnerStackAdapter().list_partnerships()["configured"] is False


def test_ai_router_exposes_models():
    router = AIRouter([AIModel("free-test", "https://example.com/v1")])
    assert router.available() == ["free-test"]
