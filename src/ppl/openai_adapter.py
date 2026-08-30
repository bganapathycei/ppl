from __future__ import annotations

import json
import os
import time
from typing import Any

from .ai_gateway import AIRequest, AIResponse


class OpenAIAdapter:
    """Minimal HTTP adapter for OpenAI-compatible chat/completions APIs.

    The adapter intentionally avoids a provider SDK so PPL keeps a small runtime
    dependency surface. It expects an API key in PPL_OPENAI_API_KEY or OPENAI_API_KEY.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 base_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("PPL_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("PPL_OPENAI_MODEL", "gpt-4.1-mini")
        self.base_url = (base_url or os.getenv("PPL_OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        if not self.api_key:
            raise RuntimeError("Missing API key. Set PPL_OPENAI_API_KEY or OPENAI_API_KEY.")

    def execute(self, request: AIRequest) -> AIResponse:
        try:
            import urllib.request
            import urllib.error
        except ImportError as exc:
            raise RuntimeError("Python urllib is required") from exc

        system = (
            "You are the PPL cognitive runtime. Return JSON only. "
            "Follow the requested schema exactly. Do not add markdown."
        )
        task = {
            "operation": request.operation,
            "instruction": request.instruction,
            "categories": request.categories,
            "schema": request.schema,
            "input": request.input_data,
        }
        body = json.dumps({
            "model": request.policy.reasoning_model if request.operation == "REASON"
                     else request.policy.classification_model if request.operation == "CLASSIFY"
                     else request.policy.extraction_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(task, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        start = time.perf_counter()
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        latency = (time.perf_counter() - start) * 1000

        message = payload["choices"][0]["message"]["content"]
        output = json.loads(message)
        usage = payload.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        cost = 0.0  # Provider pricing is intentionally not hard-coded.
        model = payload.get("model", self.model)
        return AIResponse(output, model, latency, input_tokens, output_tokens, cost, 1)
