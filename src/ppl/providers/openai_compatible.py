"""OpenAI-compatible Chat Completions transport (OpenAI, OpenRouter, Groq, Ollama)."""
from __future__ import annotations

import os
import time
from typing import Any

from ..ai_gateway import AIRequest, AIResponse
from ..production_runtime import PPLRuntimeError, RuntimeErrorCode
from .http import post_json
from .structured import json_instruction, json_schema_for_request, parse_json_object, resolve_model

PRESETS: dict[str, dict[str, str | None]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4.1-mini",
        "key_envs": "PPL_AI_API_KEY,PPL_OPENAI_API_KEY,OPENAI_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openai/gpt-4.1-mini",
        "key_envs": "PPL_AI_API_KEY,OPENROUTER_API_KEY",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "key_envs": "PPL_AI_API_KEY,GROQ_API_KEY",
    },
    "ollama": {
        "base_url": "http://127.0.0.1:11434/v1",
        "default_model": "llama3.2",
        "key_envs": "PPL_AI_API_KEY,OLLAMA_API_KEY",
    },
    "openai-compatible": {
        "base_url": None,
        "default_model": "gpt-4.1-mini",
        "key_envs": "PPL_AI_API_KEY,OPENAI_API_KEY",
    },
}


def _first_env(names: str) -> str | None:
    for name in names.split(","):
        value = os.getenv(name.strip())
        if value:
            return value
    return None


class OpenAICompatibleAdapter:
    """POST /chat/completions against any OpenAI-compatible host."""

    def __init__(
        self,
        alias: str = "openai",
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        preset = PRESETS.get(alias, PRESETS["openai-compatible"])
        self.alias = alias
        self.api_key = api_key or _first_env(str(preset["key_envs"]))
        self.base_url = (
            base_url
            or os.getenv("PPL_AI_BASE_URL")
            or os.getenv("PPL_OPENAI_BASE_URL")
            or preset["base_url"]
        )
        if self.base_url:
            self.base_url = self.base_url.rstrip("/")
        self.default_model = default_model or os.getenv("PPL_AI_MODEL") or os.getenv("PPL_OPENAI_MODEL") or preset["default_model"]
        self.extra_headers = extra_headers or {}
        if alias != "ollama" and not self.api_key:
            raise RuntimeError(
                f"{alias} API key not configured. Set one of: {preset['key_envs']}"
            )
        if not self.base_url:
            raise RuntimeError("PPL_AI_BASE_URL is required for openai-compatible providers.")

    def execute(self, request: AIRequest) -> AIResponse:
        model = resolve_model(request, self.default_model)
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are the PPL cognitive runtime. Follow the schema exactly."},
                {"role": "user", "content": json_instruction(request)},
            ],
        }
        if request.schema or request.operation == "CLASSIFY":
            if os.getenv("PPL_OPENAI_STRICT_SCHEMA") == "1" and self.alias == "openai":
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "ppl_output",
                        "strict": True,
                        "schema": json_schema_for_request(request),
                    },
                }
            else:
                payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.api_key or 'ollama'}"}
        if self.alias == "openrouter":
            headers.setdefault("HTTP-Referer", os.getenv("PPL_OPENROUTER_REFERER", "https://github.com/bganapathycei/ppl"))
            headers.setdefault("X-Title", os.getenv("PPL_OPENROUTER_TITLE", "PPL"))
        headers.update(self.extra_headers)
        started = time.perf_counter()
        parsed = post_json(f"{self.base_url}/chat/completions", payload, headers)
        latency_ms = (time.perf_counter() - started) * 1000
        try:
            message = parsed["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise PPLRuntimeError(RuntimeErrorCode.PROVIDER_ERROR, "Chat completions response missing content", retryable=False) from exc
        output = parse_json_object(message) if (request.schema or request.operation == "CLASSIFY") else {"result": message}
        usage = parsed.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        return AIResponse(output, parsed.get("model") or model, latency_ms, input_tokens, output_tokens, 0.0, 1)
