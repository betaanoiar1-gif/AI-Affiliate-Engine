from __future__ import annotations

from datetime import datetime, timezone
import html
import re
from typing import Any

import httpx

from core.cache import TTLCache
from core.domain import Signal
from core.reliability import retry
from core.security import validate_public_url


HN_BASE = "https://hacker-news.firebaseio.com/v0"


def _signal(source: str, title: str, *, momentum: float = 50.0, intent: float = 35.0, competition: float = 60.0) -> Signal:
    return Signal(source=source, keyword=html.unescape(re.sub(r"<[^>]+>", "", title)).strip(), momentum=max(0, min(100, momentum)), commercial_intent=max(0, min(100, intent)), competition=max(0, min(100, competition)), captured_at=datetime.now(timezone.utc))


class HackerNewsProvider:
    """Official public Hacker News Firebase API; no key is required."""

    def __init__(self, timeout: float = 10.0, cache: TTLCache | None = None, cache_ttl: float = 120.0):
        self.timeout = timeout
        self.cache = cache
        self.cache_ttl = max(0.0, cache_ttl)

    def _get(self, url: str) -> Any:
        key = TTLCache.key("hn", url)
        if self.cache:
            cached = self.cache.get(key)
            if cached is not None:
                return cached
        def call():
            response = httpx.get(url, timeout=self.timeout, follow_redirects=False)
            response.raise_for_status()
            return response.json()
        data = retry(call, attempts=2)
        if self.cache:
            self.cache.set(key, data, self.cache_ttl)
        return data

    def signals(self, *, limit: int = 30) -> list[Signal]:
        ids = self._get(f"{HN_BASE}/topstories.json")[: max(1, min(limit, 100))]
        result: list[Signal] = []
        for item_id in ids:
            item = self._get(f"{HN_BASE}/item/{item_id}.json") or {}
            title = item.get("title")
            if not title:
                continue
            points = float(item.get("score") or 0)
            comments = float(item.get("descendants") or 0)
            momentum = min(100.0, 35.0 + points / 8.0 + comments / 15.0)
            intent = min(100.0, 20.0 + comments / 8.0 + (25.0 if item.get("url") else 0.0))
            result.append(_signal("hackernews", title, momentum=momentum, intent=intent, competition=min(100.0, 45.0 + points / 15.0)))
        return result


class PublicRSSProvider:
    """RSS/Atom adapter for Google Trends, Reddit, YouTube channels and publisher feeds."""

    def __init__(self, feed_url: str, source: str = "rss", timeout: float = 10.0, cache: TTLCache | None = None, cache_ttl: float = 300.0):
        self.feed_url = validate_public_url(feed_url)
        self.source = source
        self.timeout = timeout
        self.cache = cache
        self.cache_ttl = max(0.0, cache_ttl)

    def signals(self, *, limit: int = 50) -> list[Signal]:
        key = TTLCache.key("rss", self.feed_url)
        if self.cache:
            cached = self.cache.get(key)
            if cached is not None:
                raw = cached.encode("utf-8")
            else:
                raw = self._fetch()
                self.cache.set(key, raw.decode("utf-8", errors="replace"), self.cache_ttl)
        else:
            raw = self._fetch()
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
        titles = re.findall(r"<title(?:\s[^>]*)?>(.*?)</title>", text, flags=re.I | re.S)
        result: list[Signal] = []
        for title in titles[1:limit + 1]:
            clean = html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", title)).strip()
            if clean:
                result.append(_signal(self.source, clean))
        return result

    def _fetch(self) -> bytes:
        def call():
            response = httpx.get(self.feed_url, timeout=self.timeout, follow_redirects=False)
            response.raise_for_status()
            return response.content
        return retry(call, attempts=2)


def default_public_feeds() -> dict[str, str]:
    return {
        "google_trends_us": "https://trends.google.com/trending/rss?geo=US",
        "google_trends_dz": "https://trends.google.com/trending/rss?geo=DZ",
        "reddit_python": "https://www.reddit.com/r/Python/.rss",
        "reddit_technology": "https://www.reddit.com/r/technology/.rss",
    }
