"""Provider-neutral structured-output helpers."""
from __future__ import annotations

import json
import os
import re
from typing import Any

from ..ai_gateway import AIRequest, ModelPolicy
from ..production_runtime import PPLRuntimeError, RuntimeErrorCode

PLACEHOLDER_MODELS = {
    "reasoning-default",
    "classification-default",
    "extraction-default",
    "fallback-default",
    "fast-reasoning",
    "fast-classifier",
    "fast-extractor",
    "fast-fallback",
}


def json_schema_for_request(request: AIRequest) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, type_name in (request.schema or {}).items():
        required.append(name)
        properties[name] = type_schema(type_name, request.categories)
    if request.operation == "CLASSIFY" and "category" not in properties:
        properties["category"] = {"type": "string", "enum": request.categories}
        required.append("category")
    if request.operation in {"CLASSIFY", "REASON"} and "confidence" not in properties:
        properties["confidence"] = {"type": "number", "minimum": 0, "maximum": 1}
        required.append("confidence")
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def type_schema(type_name: str, categories: list[str]) -> dict[str, Any]:
    t = type_name.upper()
    if t == "BOOLEAN":
        return {"type": "boolean"}
    if t == "INTEGER":
        return {"type": "integer"}
    if t == "CONFIDENCE":
        return {"type": "number", "minimum": 0, "maximum": 1}
    if t in {"NUMBER", "MONEY", "PERCENT"}:
        return {"type": "number"}
    if t == "CLASSIFICATION":
        return {"type": "string", "enum": categories}
    return {"type": "string"}


def json_instruction(request: AIRequest) -> str:
    schema = json_schema_for_request(request) if request.schema or request.operation == "CLASSIFY" else None
    parts = [
        "You are executing a PPL cognitive operation.",
        f"Operation: {request.operation}",
        f"Instruction: {request.instruction}",
        f"Input: {json.dumps(request.input_data, ensure_ascii=False, default=str)}",
    ]
    if request.categories:
        parts.append(f"Allowed categories: {json.dumps(request.categories)}")
    if schema:
        parts.append("Return JSON only. No markdown. Conform to this JSON Schema:")
        parts.append(json.dumps(schema, ensure_ascii=False))
    return "\n\n".join(parts)


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = (text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if not match:
        raise PPLRuntimeError(RuntimeErrorCode.VALIDATION_ERROR, "Model did not return a JSON object", retryable=False)
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise PPLRuntimeError(RuntimeErrorCode.VALIDATION_ERROR, "JSON payload must be an object", retryable=False)
    return parsed


def slot_model(request: AIRequest) -> str:
    if request.operation == "CLASSIFY":
        return request.policy.classification_model
    if request.operation == "EXTRACT":
        return request.policy.extraction_model
    return request.policy.reasoning_model


def resolve_model(request: AIRequest, provider_default: str | None = None) -> str:
    chosen = slot_model(request)
    env_model = os.getenv("PPL_AI_MODEL") or os.getenv("PPL_OPENAI_MODEL")
    if not chosen or chosen in PLACEHOLDER_MODELS:
        return env_model or provider_default or chosen or "unknown"
    return chosen


def substitute_policy_defaults(policy: ModelPolicy, default_model: str | None) -> ModelPolicy:
    if not default_model:
        return policy
    def sub(value: str) -> str:
        return default_model if value in PLACEHOLDER_MODELS else value
    return ModelPolicy(
        name=policy.name,
        reasoning_model=sub(policy.reasoning_model),
        classification_model=sub(policy.classification_model),
        extraction_model=sub(policy.extraction_model),
        max_retries=policy.max_retries,
        fallback_model=sub(policy.fallback_model) if policy.fallback_model in PLACEHOLDER_MODELS else policy.fallback_model,
    )
