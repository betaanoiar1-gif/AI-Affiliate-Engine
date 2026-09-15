from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any
import httpx
from core.config import settings
from core.reliability import retry
from core.security import redact_secret


@dataclass(frozen=True)
class AIModel:
    name: str
    base_url: str
    cost_per_1k_tokens: float = 0.0
    enabled: bool = True
    supports_json_mode: bool = True
    key_env: str = "AI_API_KEY"
    provider: str = "custom"


class AIRouter:
    """OpenAI-compatible router with per-provider keys, retries, JSON fallback and zero-cost-first ordering."""
    def __init__(self, models: list[AIModel] | None = None):
        self.models = models or self._from_env()
        self.spent = 0.0

    def _from_env(self) -> list[AIModel]:
        # Explicit AI_* configuration remains supported. Free-tier providers are appended only when configured.
        models: list[AIModel] = []
        base = os.getenv("AI_BASE_URL", "").strip().rstrip("/")
        model = os.getenv("AI_MODEL", "").strip()
        if base and model:
            models.append(AIModel(model, base, float(os.getenv("AI_COST_PER_1K", "0") or 0), key_env="AI_API_KEY", provider="custom"))
        free_profiles = (
            ("openrouter_free", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "OPENROUTER_MODEL"),
            ("gemini_free", "https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY", "GEMINI_MODEL"),
            ("groq_free", "https://api.groq.com/openai/v1", "GROQ_API_KEY", "GROQ_MODEL"),
            ("huggingface_free", "https://router.huggingface.co/v1", "HF_TOKEN", "HF_MODEL"),
        )
        for provider, url, key_env, model_env in free_profiles:
            key = os.getenv(key_env, "").strip()
            selected_model = os.getenv(model_env, "").strip()
            if key and selected_model:
                models.append(AIModel(selected_model, url, 0.0, key_env=key_env, provider=provider))
        return models

    def available(self) -> list[str]:
        return [f"{m.provider}:{m.name}" for m in self.models if m.enabled and os.getenv(m.key_env, "").strip()]

    def _key(self, model: AIModel, api_key: str | None) -> str:
        key = api_key or os.getenv(model.key_env, "")
        if not key:
            raise RuntimeError(f"AI provider key is not configured: {model.provider}")
        return key

    def generate_json(self, *, system: str, user: str, api_key: str | None = None, max_tokens: int = 800) -> dict[str, Any]:
        if not self.models:
            raise RuntimeError("no AI models configured")
        if settings.ai_monthly_budget and self.spent >= settings.ai_monthly_budget:
            raise RuntimeError("AI budget exhausted")
        last: Exception | None = None
        for model in self.models:
            if not model.enabled:
                continue
            try:
                key = self._key(model, api_key if model.provider == "custom" else None)
                base_payload = {"model": model.name, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "temperature": 0.2, "max_tokens": max_tokens}
                payloads = [{**base_payload, "response_format": {"type": "json_object"}}, base_payload] if model.supports_json_mode else [base_payload]
                data = None
                for payload in payloads:
                    def call(payload=payload):
                        response = httpx.post(f"{model.base_url.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload, timeout=settings.request_timeout_seconds, follow_redirects=False)
                        if response.status_code == 429 or response.status_code >= 500:
                            raise RuntimeError(f"AI temporary failure: {response.status_code}")
                        response.raise_for_status()
                        return response.json()
                    try:
                        data = retry(call, attempts=2)
                        break
                    except Exception as exc:
                        last = exc
                if data is None:
                    continue
                usage = data.get("usage") or {}
                tokens = float(usage.get("total_tokens") or 0)
                self.spent += tokens / 1000 * model.cost_per_1k_tokens
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ValueError("AI response JSON must be an object")
                return parsed
            except Exception as exc:
                last = exc
        raise RuntimeError(f"all AI models failed: {redact_secret(str(last))}")
