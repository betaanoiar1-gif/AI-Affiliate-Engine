from __future__ import annotations

import os
from dataclasses import dataclass

from .router import AIModel


@dataclass(frozen=True)
class FreeAIProfile:
    id: str
    base_url: str
    key_env: str
    model_env: str
    default_model: str
    notes: str


FREE_AI_PROFILES = (
    FreeAIProfile("openrouter_free", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "OPENROUTER_MODEL", "", "Use a model explicitly marked free by OpenRouter; model availability changes."),
    FreeAIProfile("gemini_free", "https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY", "GEMINI_MODEL", "", "Use the currently free Gemini model/quota visible in AI Studio."),
    FreeAIProfile("groq_free", "https://api.groq.com/openai/v1", "GROQ_API_KEY", "GROQ_MODEL", "", "Use a currently free/eligible Groq model and respect provider rate limits."),
    FreeAIProfile("huggingface_free", "https://router.huggingface.co/v1", "HF_TOKEN", "HF_MODEL", "", "Free users receive limited monthly inference-provider credit; never assume unlimited use."),
)


def free_models_from_env() -> list[AIModel]:
    models: list[AIModel] = []
    for profile in FREE_AI_PROFILES:
        key = os.getenv(profile.key_env, "").strip()
        model = os.getenv(profile.model_env, profile.default_model).strip()
        if not key or not model:
            continue
        models.append(AIModel(name=model, base_url=profile.base_url, cost_per_1k_tokens=0.0, enabled=True, supports_json_mode=True))
    return models


def configured_free_providers() -> list[str]:
    return [p.id for p in FREE_AI_PROFILES if os.getenv(p.key_env, "").strip() and os.getenv(p.model_env, "").strip()]
