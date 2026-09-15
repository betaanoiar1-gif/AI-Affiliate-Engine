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


# Free means no paid SaaS subscription is required for the base path.
# Free-tier/public endpoints can have quotas, terms, or availability changes.
# Libraries are listed as free because the project can run them without a SaaS bill.
FREE_FIRST_CATALOG: tuple[ToolSpec, ...] = (
    # Discovery / trend data
    ToolSpec("hackernews_api", "trend", "public REST", "free", False, True, "Near-real-time technology/product signals", "high", ("rss",)),
    ToolSpec("google_trends_rss", "trend", "public RSS", "free", False, True, "Search-trend discovery without a paid provider", "medium", ("rss", "hackernews_api")),
    ToolSpec("reddit_rss", "trend", "public RSS", "free", False, True, "Community topic discovery where feeds are available", "medium", ("rss",)),
    ToolSpec("youtube_rss", "trend", "public RSS", "free", False, True, "Channel/video discovery without paid search APIs", "medium", ("youtube_data_api",)),
    ToolSpec("rss", "trend", "HTTP RSS/Atom", "free", False, True, "Universal publisher/news feed ingestion", "high"),
    ToolSpec("github_public_api", "trend", "public REST", "free", False, True, "Public repository/activity signals", "high", ("rss",)),
    ToolSpec("wikipedia_api", "research", "public REST", "free", False, True, "Public encyclopedia metadata and page signals", "high", ("rss",)),

    # Web acquisition / extraction
    ToolSpec("httpx", "web", "Python HTTP client", "free", False, False, "Fast public HTTP acquisition", "high", ("playwright",)),
    ToolSpec("beautifulsoup4", "web", "HTML parser", "free", False, False, "Deterministic HTML extraction after permitted fetch", "high", ("trafilatura",)),
    ToolSpec("trafilatura", "web", "content extractor", "free", False, False, "Article/main-content extraction", "high", ("beautifulsoup4",)),
    ToolSpec("playwright", "browser", "local browser", "free", False, False, "Browser automation for permitted public workflows", "high", ("crawlee",)),
    ToolSpec("crawlee", "browser", "HTTP/browser crawler", "free", False, False, "Resilient crawling using HTTP or browsers", "high", ("playwright", "rss")),

    # Media / content utilities
    ToolSpec("ffmpeg", "media", "local CLI", "free", False, False, "Video/audio conversion, muxing and normalization", "high"),
    ToolSpec("yt_dlp", "media", "CLI/library", "free", False, False, "Metadata/media extraction where platform terms permit", "high", ("youtube_rss",)),
    ToolSpec("pillow", "media", "Python library", "free", False, False, "Image inspection, resizing and transformations", "high"),

    # Storage / analytics / local infrastructure
    ToolSpec("sqlite", "storage", "embedded database", "free", False, False, "Durable operational state and event storage", "high"),
    ToolSpec("duckdb", "analytics", "embedded analytical database", "free", False, False, "Local analytical queries and batch reporting", "high", ("sqlite",)),
    ToolSpec("parquet", "analytics", "columnar file format", "free", False, False, "Portable analytical snapshots", "high", ("sqlite",)),
    ToolSpec("python_cache", "infrastructure", "local cache", "free", False, False, "Avoid repeated network calls and quota waste", "high"),

    # Observability / quality / security
    ToolSpec("pytest", "quality", "local test runner", "free", False, False, "Automated regression and integration testing", "high"),
    ToolSpec("ruff", "quality", "local linter/formatter", "free", False, False, "Fast Python linting and formatting", "high"),
    ToolSpec("bandit", "security", "local SAST", "free", False, False, "Python security checks", "high"),
    ToolSpec("pip_audit", "security", "dependency scanner", "free", False, False, "Known-vulnerability checks for Python dependencies", "high"),

    # Affiliate / platform adapters
    ToolSpec("awin", "affiliate", "official API/feed", "credential-required", True, True, "Affiliate offers, feeds and publisher data when account access exists", "high", ("partnerstack",)),
    ToolSpec("partnerstack", "affiliate", "official API", "credential-required", True, True, "Partner-program data when account access exists", "medium", ("awin",)),
    ToolSpec("youtube_data_api", "platform", "official API", "free-tier", True, True, "Official YouTube metadata/search/publishing surface", "high", ("youtube_rss",)),

    # Optional AI providers are deliberately isolated from the non-AI catalog.
    ToolSpec("openrouter_free", "ai", "OpenAI-compatible", "free-tier", True, True, "Access to currently offered free models behind one router", "medium", ("gemini_free", "groq_free", "huggingface_free")),
    ToolSpec("gemini_free", "ai", "OpenAI-compatible", "free-tier", True, True, "Cloud LLM fallback with provider quota", "high", ("openrouter_free", "groq_free")),
    ToolSpec("groq_free", "ai", "OpenAI-compatible", "free-tier", True, True, "Fast cloud inference when free quota is available", "high", ("openrouter_free", "gemini_free")),
    ToolSpec("huggingface_free", "ai", "Inference Providers", "free-tier", True, True, "Model/provider catalog with included credit", "medium", ("openrouter_free",)),
)


def catalog(*, category: str | None = None, only_no_payment: bool = False, exclude_ai: bool = False) -> list[ToolSpec]:
    items = [x for x in FREE_FIRST_CATALOG if x.enabled]
    if category:
        items = [x for x in items if x.category == category]
    if only_no_payment:
        items = [x for x in items if x.cost == "free"]
    if exclude_ai:
        items = [x for x in items if x.category != "ai"]
    return items


def get_tool(tool_id: str) -> ToolSpec:
    for tool in FREE_FIRST_CATALOG:
        if tool.id == tool_id:
            return tool
    raise KeyError(tool_id)


def fallback_chain(tool_id: str) -> tuple[str, ...]:
    tool = get_tool(tool_id)
    return (tool.id, *tool.fallback)
