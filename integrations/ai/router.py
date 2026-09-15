from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any
import httpx
from core.config import settings
from core.reliability import retry_call
from core.security import redact_secret


@dataclass(frozen=True)
class AIModel:
    name: str
    base_url: str
    cost_per_1k_tokens: float = 0.0
    enabled: bool = True


class AIRouter:
    """OpenAI-compatible router with deterministic fallback, budget and provider isolation."""
    def __init__(self, models: list[AIModel] | None = None):
        self.models = models or self._from_env()
        self.spent = 0.0

    def _from_env(self) -> list[AIModel]:
        base = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        model = os.getenv("AI_MODEL", "gpt-4o-mini")
        return [AIModel(model, base, float(os.getenv("AI_COST_PER_1K", "0")))]

    def available(self) -> list[str]:
        return [m.name for m in self.models if m.enabled]

    def generate_json(self, *, system: str, user: str, api_key: str | None = None, max_tokens: int = 800) -> dict[str, Any]:
        if not self.models:
            raise RuntimeError("no AI models configured")
        if settings.ai_monthly_budget and self.spent >= settings.ai_monthly_budget:
            raise RuntimeError("AI budget exhausted")
        last: Exception | None = None
        for model in self.models:
            key = api_key or os.getenv("AI_API_KEY")
            if not key:
                raise RuntimeError("AI provider key is not configured")
            payload = {"model": model.name, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "temperature": 0.2, "max_tokens": max_tokens, "response_format": {"type": "json_object"}}
            def call():
                response = httpx.post(f"{model.base_url}/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload, timeout=settings.request_timeout_seconds)
                if response.status_code == 429 or response.status_code >= 500:
                    raise RuntimeError(f"AI temporary failure: {response.status_code}")
                response.raise_for_status()
                return response.json()
            try:
                data = retry_call(call, attempts=2)
                usage = data.get("usage") or {}
                tokens = float(usage.get("total_tokens") or 0)
                self.spent += tokens / 1000 * model.cost_per_1k_tokens
                import json
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
            except Exception as exc:
                last = exc
        raise RuntimeError(f"all AI models failed: {redact_secret(str(last))}")
