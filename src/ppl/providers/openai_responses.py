"""Optional OpenAI Responses API adapter (`PPL_AI_PROVIDER=openai-responses`)."""
from __future__ import annotations

import os
import time

from ..ai_gateway import AIRequest, AIResponse
from ..production_runtime import PPLRuntimeError, RuntimeErrorCode
from .http import post_json
from .structured import json_instruction, json_schema_for_request, parse_json_object, resolve_model


class OpenAIResponsesAdapter:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("PPL_AI_API_KEY") or os.getenv("PPL_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("PPL_AI_BASE_URL") or os.getenv("PPL_OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.default_model = os.getenv("PPL_AI_MODEL") or os.getenv("PPL_OPENAI_MODEL") or "gpt-4.1-mini"
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured. Set PPL_OPENAI_API_KEY or OPENAI_API_KEY.")

    def execute(self, request: AIRequest) -> AIResponse:
        model = resolve_model(request, self.default_model)
        payload: dict = {
            "model": model,
            "input": json_instruction(request),
        }
        if request.schema or request.operation == "CLASSIFY":
            payload["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": "ppl_output",
                    "schema": json_schema_for_request(request),
                    "strict": True,
                }
            }
        started = time.perf_counter()
        parsed = post_json(
            f"{self.base_url}/responses",
            payload,
            {"Authorization": f"Bearer {self.api_key}"},
        )
        latency_ms = (time.perf_counter() - started) * 1000
        output_text = self._extract_output_text(parsed)
        output = parse_json_object(output_text) if (request.schema or request.operation == "CLASSIFY") else {"result": output_text}
        usage = parsed.get("usage") or {}
        input_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
        return AIResponse(output, parsed.get("model") or model, latency_ms, input_tokens, output_tokens, 0.0, 1)

    def _extract_output_text(self, response: dict) -> str:
        if isinstance(response.get("output_text"), str):
            return response["output_text"]
        for item in response.get("output") or []:
            for content in item.get("content") or []:
                if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                    return content["text"]
        raise PPLRuntimeError(RuntimeErrorCode.PROVIDER_ERROR, "OpenAI Responses payload missing output text", retryable=False)
