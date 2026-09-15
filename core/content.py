from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass
from .domain import ContentPlan


@dataclass(frozen=True)
class ContentCheck:
    allowed: bool
    score: float
    reasons: list[str]
    fingerprint: str


def fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def validate_content(plan: ContentPlan, *, seen_fingerprints: set[str] | None = None) -> ContentCheck:
    reasons: list[str] = []
    text = " ".join([plan.angle, plan.hook, *plan.body_outline, plan.cta])
    if not plan.hook.strip():
        reasons.append("missing hook")
    if len(plan.hook.strip()) < 8:
        reasons.append("hook is too short")
    if not plan.body_outline:
        reasons.append("missing body outline")
    if not plan.disclosure.strip():
        reasons.append("affiliate disclosure missing")
    fp = fingerprint(text)
    if seen_fingerprints and fp in seen_fingerprints:
        reasons.append("duplicate content fingerprint")
    score = max(0.0, 100.0 - 20.0 * len(reasons))
    return ContentCheck(allowed=not reasons, score=score, reasons=reasons, fingerprint=fp)
