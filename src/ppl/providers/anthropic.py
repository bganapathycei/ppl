"""Native Anthropic Messages API adapter."""
from __future__ import annotations

import os
import time

from ..ai_gateway import AIRequest, AIResponse
from ..production_runtime import PPLRuntimeError, RuntimeErrorCode
from .http import post_json
from .structured import json_instruction, parse_json_object, resolve_model


class AnthropicAdapter:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("PPL_AI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = (base_url or os.getenv("PPL_AI_BASE_URL") or "https://api.anthropic.com").rstrip("/")
        self.default_model = os.getenv("PPL_AI_MODEL") or "claude-sonnet-4-5"
        self.version = os.getenv("PPL_ANTHROPIC_VERSION", "2023-06-01")
        if not self.api_key:
            raise RuntimeError("Anthropic API key not configured. Set ANTHROPIC_API_KEY or PPL_AI_API_KEY.")

    def execute(self, request: AIRequest) -> AIResponse:
        model = resolve_model(request, self.default_model)
        payload = {
            "model": model,
            "max_tokens": int(os.getenv("PPL_AI_MAX_TOKENS", "1024")),
            "system": "You are the PPL cognitive runtime. Return JSON only when a schema is provided.",
            "messages": [{"role": "user", "content": json_instruction(request)}],
        }
        started = time.perf_counter()
        parsed = post_json(
            f"{self.base_url}/v1/messages",
            payload,
            {
                "x-api-key": self.api_key,
                "anthropic-version": self.version,
            },
        )
        latency_ms = (time.perf_counter() - started) * 1000
        text = self._extract_text(parsed)
        output = parse_json_object(text) if (request.schema or request.operation == "CLASSIFY") else {"result": text}
        usage = parsed.get("usage") or {}
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        return AIResponse(output, parsed.get("model") or model, latency_ms, input_tokens, output_tokens, 0.0, 1)

    def _extract_text(self, response: dict) -> str:
        for block in response.get("content") or []:
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                return block["text"]
        raise PPLRuntimeError(RuntimeErrorCode.PROVIDER_ERROR, "Anthropic response missing text content", retryable=False)
