from __future__ import annotations
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import httpx
from core.domain import Signal
from core.security import validate_public_url


class RSSKeywordProvider:
    """Generic RSS trend source; it consumes feeds explicitly supplied by the operator."""
    def __init__(self, feed_url: str, source: str = "rss", timeout: float = 15.0):
        self.feed_url = validate_public_url(feed_url)
        self.source = source
        self.timeout = timeout

    def signals(self, *, limit: int = 50) -> list[Signal]:
        response = httpx.get(self.feed_url, timeout=self.timeout, follow_redirects=False)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = root.findall(".//item")[:limit]
        now = datetime.now(timezone.utc)
        result: list[Signal] = []
        for item in items:
            title = (item.findtext("title") or "").strip()
            if not title:
                continue
            result.append(Signal(source=self.source, keyword=title, momentum=50.0, commercial_intent=30.0, competition=60.0, captured_at=now))
        return result
