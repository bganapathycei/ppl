from __future__ import annotations

import json
import os
import time
from typing import Any

from .ai_gateway import AIRequest, AIResponse, ModelAdapter


class OpenAIModelAdapter:
    """OpenAI adapter using the public HTTP API without a hard SDK dependency."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("PPL_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("PPL_OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured. Set PPL_OPENAI_API_KEY or OPENAI_API_KEY.")

    def execute(self, request: AIRequest) -> AIResponse:
        try:
            import urllib.request
        except ImportError as exc:
            raise RuntimeError("Python urllib is required for the OpenAI adapter") from exc

        model = self._select_model(request)
        payload = {
            "model": model,
            "input": self._build_input(request),
        }
        if request.schema:
            payload["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": "ppl_output",
                    "schema": self._json_schema(request),
                    "strict": True,
                }
            }
        body = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            f"{self.base_url}/responses",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        start = time.perf_counter()
        with urllib.request.urlopen(http_request, timeout=60) as response:
            raw = response.read().decode("utf-8")
        latency_ms = (time.perf_counter() - start) * 1000
        parsed = json.loads(raw)
        output_text = self._extract_output_text(parsed)
        output = json.loads(output_text) if request.schema else {"result": output_text}
        usage = parsed.get("usage", {}) or {}
        input_tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
        output_tokens = int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0)
        return AIResponse(output, model, latency_ms, input_tokens, output_tokens, 0.0, 1)

    def _select_model(self, request: AIRequest) -> str:
        if request.operation == "CLASSIFY":
            return request.policy.classification_model
        if request.operation == "EXTRACT":
            return request.policy.extraction_model
        return request.policy.reasoning_model

    def _build_input(self, request: AIRequest) -> str:
        parts = [
            "You are executing a PPL cognitive operation.",
            f"Operation: {request.operation}",
            f"Instruction: {request.instruction}",
            f"Input: {json.dumps(request.input_data, ensure_ascii=False)}",
        ]
        if request.categories:
            parts.append(f"Allowed categories: {json.dumps(request.categories)}")
        return "\n\n".join(parts)

    def _json_schema(self, request: AIRequest) -> dict[str, Any]:
        properties: dict[str, Any] = {}
        required = []
        for name, type_name in request.schema.items():
            required.append(name)
            properties[name] = self._type_schema(type_name, request.categories)
        if request.operation == "CLASSIFY" and "category" not in properties:
            properties["category"] = {"type": "string", "enum": request.categories}
            required.append("category")
        if request.operation in {"CLASSIFY", "REASON"} and "confidence" not in properties:
            properties["confidence"] = {"type": "number", "minimum": 0, "maximum": 1}
            required.append("confidence")
        return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}

    def _type_schema(self, type_name: str, categories: list[str]) -> dict[str, Any]:
        t = type_name.upper()
        if t == "BOOLEAN": return {"type": "boolean"}
        if t == "INTEGER": return {"type": "integer"}
        if t in {"NUMBER", "MONEY", "PERCENT", "CONFIDENCE"}: return {"type": "number", "minimum": 0 if t == "CONFIDENCE" else None}
        if t == "CLASSIFICATION": return {"type": "string", "enum": categories}
        return {"type": "string"}

    def _extract_output_text(self, response: dict[str, Any]) -> str:
        if isinstance(response.get("output_text"), str):
            return response["output_text"]
        for item in response.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                    return content["text"]
        raise RuntimeError("OpenAI response did not contain output text")


def gateway_from_environment(local_gateway):
    provider = os.getenv("PPL_AI_PROVIDER", "local").lower()
    if provider == "openai":
        from .ai_gateway import AIGateway
        return AIGateway(OpenAIModelAdapter())
    return local_gateway
