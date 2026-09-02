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


def _resolve_profile(file_cfg: dict) -> dict | None:
    """Resolve active provider profile from env or ppl.providers.json."""
    profile_name = os.getenv("PPL_PROFILE") or file_cfg.get("active_profile")
    profiles = file_cfg.get("profiles")
    if not profile_name or not isinstance(profiles, dict):
        return None
    profile = profiles.get(profile_name)
    return profile if isinstance(profile, dict) else None


def resolve_config() -> dict:
    """Return resolved provider configuration (env overrides file)."""
    file_path = Path(os.getenv("PPL_PROVIDERS_FILE", "ppl.providers.json"))
    file_cfg = load_providers_file(file_path)
    profile = _resolve_profile(file_cfg)
    provider = (
        os.getenv("PPL_AI_PROVIDER")
        or (profile or {}).get("provider")
        or file_cfg.get("provider")
        or "local"
    )
    model = (
        os.getenv("PPL_AI_MODEL")
        or os.getenv("PPL_OPENAI_MODEL")
        or (profile or {}).get("model")
        or file_cfg.get("model")
    )
    base_url = (
        os.getenv("PPL_AI_BASE_URL")
        or os.getenv("PPL_OPENAI_BASE_URL")
        or (profile or {}).get("base_url")
        or file_cfg.get("base_url")
    )
    api_key = (
        os.getenv("PPL_AI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or (profile or {}).get("api_key")
        or file_cfg.get("api_key")
    )
    return {
        "provider": str(provider).strip().lower(),
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
        "profile": os.getenv("PPL_PROFILE") or file_cfg.get("active_profile"),
        "config_file": str(file_path) if file_path.exists() else None,
        "source": "environment" if os.getenv("PPL_AI_PROVIDER") else ("profile" if profile else "file" if file_cfg else "default"),
    }


def mask_api_key(key: str | None) -> str | None:
    if not key:
        return None
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def public_config() -> dict:
    """Provider config safe for CLI/editor display."""
    cfg = resolve_config()
    return {
        "provider": cfg["provider"],
        "model": cfg["model"],
        "base_url": cfg["base_url"],
        "api_key_set": bool(cfg["api_key"]),
        "api_key_masked": mask_api_key(cfg["api_key"]),
        "profile": cfg.get("profile"),
        "config_file": cfg.get("config_file"),
        "source": cfg.get("source"),
        "supported": list(SUPPORTED),
    }


def _config() -> dict:
    return resolve_config()


def test_provider() -> dict:
    """Run a lightweight cognitive health check against the configured adapter."""
    from .ai_gateway import AIRequest, ModelPolicy

    adapter = build_adapter()
    req = AIRequest(
        "CLASSIFY",
        "Classify the input into the allowed categories.",
        {"input": "hello"},
        {"category": "CLASSIFICATION", "confidence": "CONFIDENCE"},
        ["GREETING", "OTHER"],
        ModelPolicy(),
    )
    start = __import__("time").perf_counter()
    response = adapter.execute(req)
    latency_ms = (__import__("time").perf_counter() - start) * 1000
    cfg = resolve_config()
    return {
        "ok": True,
        "provider": cfg["provider"],
        "model": response.model,
        "latency_ms": round(latency_ms, 2),
        "output": response.output,
    }


def apply_program_environment(environments: list[dict] | None) -> None:
    """Apply ENVIRONMENT block from program as provider profile when PPL_PROFILE is unset."""
    if os.getenv("PPL_PROFILE") or not environments:
        return
    name = environments[0].get("name")
    if name:
        os.environ["PPL_PROFILE"] = str(name)


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
