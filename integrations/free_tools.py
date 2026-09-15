from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CostMode = Literal["free", "free-tier", "credential-required", "paid-fallback"]


@dataclass(frozen=True)
class ToolSpec:
    id: str
    category: str
    access: str
    cost: CostMode
    credentials: bool
    cloud: bool
    purpose: str
    reliability: str
    fallback: tuple[str, ...] = ()
    enabled: bool = True


# "Free" means no paid SaaS subscription is required for the base path.
# Free tiers and public endpoints can have quotas, terms, or change without notice.
FREE_FIRST_CATALOG: tuple[ToolSpec, ...] = (
    ToolSpec("hackernews_api", "trend", "public REST", "free", False, True, "Near-real-time technology/product signals", "high", ("rss",)),
    ToolSpec("google_trends_rss", "trend", "public RSS", "free", False, True, "Search-trend discovery without a paid provider", "medium", ("rss", "hackernews_api")),
    ToolSpec("reddit_rss", "trend", "public RSS", "free", False, True, "Community topic discovery where feeds are available", "medium", ("rss",)),
    ToolSpec("youtube_rss", "trend", "public RSS", "free", False, True, "Channel/video discovery without paid search APIs", "medium", ("youtube_data_api",)),
    ToolSpec("rss", "trend", "HTTP RSS/Atom", "free", False, True, "Universal publisher/news feed ingestion", "high"),
    ToolSpec("openrouter_free", "ai", "OpenAI-compatible", "free-tier", True, True, "Access to currently offered free models behind one router", "medium", ("gemini_free", "groq_free", "huggingface_free")),
    ToolSpec("gemini_free", "ai", "OpenAI-compatible", "free-tier", True, True, "Cloud LLM fallback with provider quota", "high", ("openrouter_free", "groq_free")),
    ToolSpec("groq_free", "ai", "OpenAI-compatible", "free-tier", True, True, "Fast cloud inference when free quota is available", "high", ("openrouter_free", "gemini_free")),
    ToolSpec("huggingface_free", "ai", "Inference Providers", "free-tier", True, True, "Large model/provider catalog with small included credit", "medium", ("openrouter_free",)),
    ToolSpec("playwright", "browser", "local browser", "free", False, True, "Browser automation for permitted public workflows", "high", ("crawlee",)),
    ToolSpec("crawlee", "browser", "HTTP/browser crawler", "free", False, True, "Resilient crawling using HTTP or browsers", "high", ("playwright", "rss")),
    ToolSpec("yt_dlp", "media", "CLI/library", "free", False, True, "Metadata/media extraction where platform terms permit", "high", ("youtube_rss",)),
    ToolSpec("youtube_data_api", "platform", "official API", "free-tier", True, True, "Official YouTube metadata/search/publishing surface", "high", ("youtube_rss",)),
)


def catalog(*, category: str | None = None, only_no_payment: bool = False) -> list[ToolSpec]:
    items = [x for x in FREE_FIRST_CATALOG if x.enabled]
    if category:
        items = [x for x in items if x.category == category]
    if only_no_payment:
        items = [x for x in items if x.cost == "free"]
    return items


def get_tool(tool_id: str) -> ToolSpec:
    for tool in FREE_FIRST_CATALOG:
        if tool.id == tool_id:
            return tool
    raise KeyError(tool_id)


def fallback_chain(tool_id: str) -> tuple[str, ...]:
    tool = get_tool(tool_id)
    return (tool.id, *tool.fallback)
