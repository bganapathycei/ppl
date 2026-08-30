"""Backward-compatible re-export of the OpenAI adapters."""
from __future__ import annotations

from .ai_gateway import AIGateway, LocalModelAdapter
from .provider import build_adapter
from .providers.openai_compatible import OpenAICompatibleAdapter
from .providers.openai_responses import OpenAIResponsesAdapter

OpenAIModelAdapter = OpenAIResponsesAdapter


def gateway_from_environment(local_gateway):
    adapter = build_adapter()
    if isinstance(adapter, LocalModelAdapter):
        return local_gateway
    return AIGateway(adapter)


__all__ = ["OpenAIModelAdapter", "OpenAICompatibleAdapter", "OpenAIResponsesAdapter", "gateway_from_environment"]
