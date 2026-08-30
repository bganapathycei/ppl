"""Native Google Gemini generateContent adapter."""
from __future__ import annotations

import os
import time

from ..ai_gateway import AIRequest, AIResponse
from ..production_runtime import PPLRuntimeError, RuntimeErrorCode
from .http import post_json
from .structured import json_instruction, json_schema_for_request, parse_json_object, resolve_model


class GoogleAdapter:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("PPL_AI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.base_url = (base_url or os.getenv("PPL_AI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self.default_model = os.getenv("PPL_AI_MODEL") or "gemini-2.5-flash"
        if not self.api_key:
            raise RuntimeError("Google API key not configured. Set GOOGLE_API_KEY, GEMINI_API_KEY, or PPL_AI_API_KEY.")

    def execute(self, request: AIRequest) -> AIResponse:
        model = resolve_model(request, self.default_model)
        generation: dict = {}
        if request.schema or request.operation == "CLASSIFY":
            generation["responseMimeType"] = "application/json"
            generation["responseSchema"] = json_schema_for_request(request)
        payload = {
            "contents": [{"role": "user", "parts": [{"text": json_instruction(request)}]}],
        }
        if generation:
            payload["generationConfig"] = generation
        started = time.perf_counter()
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        parsed = post_json(url, payload, {})
        latency_ms = (time.perf_counter() - started) * 1000
        text = self._extract_text(parsed)
        output = parse_json_object(text) if (request.schema or request.operation == "CLASSIFY") else {"result": text}
        usage = parsed.get("usageMetadata") or {}
        input_tokens = int(usage.get("promptTokenCount") or 0)
        output_tokens = int(usage.get("candidatesTokenCount") or usage.get("totalTokenCount") or 0)
        return AIResponse(output, model, latency_ms, input_tokens, output_tokens, 0.0, 1)

    def _extract_text(self, response: dict) -> str:
        try:
            parts = response["candidates"][0]["content"]["parts"]
            texts = [p.get("text") for p in parts if isinstance(p.get("text"), str)]
            if texts:
                return "".join(texts)
        except (KeyError, IndexError, TypeError):
            pass
        raise PPLRuntimeError(RuntimeErrorCode.PROVIDER_ERROR, "Google response missing text parts", retryable=False)
