from __future__ import annotations

import os

from .ai_gateway import LocalModelAdapter, ModelAdapter
from .real_ai import OpenAIModelAdapter


def build_adapter() -> ModelAdapter:
    provider = os.getenv("PPL_AI_PROVIDER", "local").strip().lower()
    if provider in {"local", "mock", ""}:
        return LocalModelAdapter()
    if provider in {"openai", "openai-compatible"}:
        return OpenAIModelAdapter()
    raise ValueError(f"Unsupported PPL_AI_PROVIDER: {provider}. Use 'local' or 'openai'.")
