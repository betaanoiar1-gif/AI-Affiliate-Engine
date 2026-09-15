from core.content import fingerprint, validate_content
from core.domain import ContentPlan


def plan(**kw):
    data = dict(offer_id="o", platform="youtube", angle="A useful guide", hook="Three useful things", body_outline=["one", "two"], disclosure="Affiliate disclosure", cta="Learn more")
    data.update(kw)
    return ContentPlan(**data)


def test_content_gate_accepts_complete_plan():
    result = validate_content(plan())
    assert result.allowed is True
    assert result.score == 100


def test_content_gate_detects_duplicate_and_missing_disclosure():
    p = plan(disclosure="")
    result = validate_content(p, seen_fingerprints={fingerprint(" ".join([p.angle, p.hook, *p.body_outline, p.cta]))})
    assert result.allowed is False
    assert "duplicate content fingerprint" in result.reasons
    assert "affiliate disclosure missing" in result.reasons
