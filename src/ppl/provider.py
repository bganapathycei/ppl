"""Provider registry: env + optional ppl.providers.json. .ppl source stays vendor-free."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .ai_gateway import LocalModelAdapter, ModelAdapter
from .providers.anthropic import AnthropicAdapter
from .providers.google import GoogleAdapter
from .providers.openai_compatible import OpenAICompatibleAdapter
from .providers.openai_responses import OpenAIResponsesAdapter

SUPPORTED = (
    "local",
    "mock",
    "openai",
    "openai-compatible",
    "openai-responses",
    "openrouter",
    "groq",
    "ollama",
    "anthropic",
    "google",
    "gemini",
)


def load_providers_file(path: str | Path | None = None) -> dict:
    file_path = Path(path or os.getenv("PPL_PROVIDERS_FILE", "ppl.providers.json"))
    if not file_path.exists():
        return {}
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _config() -> dict:
    file_cfg = load_providers_file()
    provider = os.getenv("PPL_AI_PROVIDER") or file_cfg.get("provider") or "local"
    model = os.getenv("PPL_AI_MODEL") or os.getenv("PPL_OPENAI_MODEL") or file_cfg.get("model")
    base_url = os.getenv("PPL_AI_BASE_URL") or os.getenv("PPL_OPENAI_BASE_URL") or file_cfg.get("base_url")
    api_key = os.getenv("PPL_AI_API_KEY") or file_cfg.get("api_key")
    return {
        "provider": str(provider).strip().lower(),
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
    }


def build_adapter() -> ModelAdapter:
    cfg = _config()
    name = cfg["provider"]
    if name in {"local", "mock", ""}:
        return LocalModelAdapter()
    if name in {"openai", "openai-compatible", "openrouter", "groq", "ollama"}:
        alias = "openai-compatible" if name == "openai-compatible" else name
        return OpenAICompatibleAdapter(
            alias=alias,
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
            default_model=cfg["model"],
        )
    if name == "openai-responses":
        return OpenAIResponsesAdapter(api_key=cfg["api_key"], base_url=cfg["base_url"])
    if name == "anthropic":
        return AnthropicAdapter(api_key=cfg["api_key"], base_url=cfg["base_url"])
    if name in {"google", "gemini"}:
        return GoogleAdapter(api_key=cfg["api_key"], base_url=cfg["base_url"])
    raise ValueError(
        f"Unsupported PPL_AI_PROVIDER: {name}. Use one of: {', '.join(SUPPORTED)}"
    )
