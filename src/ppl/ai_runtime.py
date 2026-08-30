from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ai_gateway import AIGateway, AIRequest, AIResponse, ModelAdapter, ModelPolicy


class CognitiveRuntimeError(RuntimeError):
    pass


class SchemaValidationError(CognitiveRuntimeError):
    pass


@dataclass
class ExecutionTelemetry:
    operation: str
    model: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    attempts: int
    validated: bool


def validate_output(response: AIResponse, request: AIRequest) -> None:
    output = response.output
    if not isinstance(output, dict):
        raise SchemaValidationError("Cognitive output must be an object")
    for field_name, type_name in request.schema.items():
        if field_name not in output:
            raise SchemaValidationError(f"Missing required output field: {field_name}")
        value = output[field_name]
        normalized = type_name.upper()
        if normalized == "TEXT" and not isinstance(value, str):
            raise SchemaValidationError(f"{field_name} must be TEXT")
        if normalized == "BOOLEAN" and not isinstance(value, bool):
            raise SchemaValidationError(f"{field_name} must be BOOLEAN")
        if normalized in {"NUMBER", "MONEY", "PERCENT"} and (not isinstance(value, (int, float)) or isinstance(value, bool)):
            raise SchemaValidationError(f"{field_name} must be NUMBER-like")
        if normalized == "INTEGER" and (not isinstance(value, int) or isinstance(value, bool)):
            raise SchemaValidationError(f"{field_name} must be INTEGER")
        if normalized == "CONFIDENCE":
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= float(value) <= 1:
                raise SchemaValidationError(f"{field_name} must be CONFIDENCE in [0,1]")
    if request.operation == "CLASSIFY" and "category" in output and output["category"] not in request.categories:
        raise SchemaValidationError(f"Invalid classification category: {output['category']}")


class CognitiveRuntime:
    """Provider-neutral cognitive runtime with retry/fallback and telemetry."""

    def __init__(self, adapter: ModelAdapter | None = None) -> None:
        self.gateway = AIGateway(adapter)
        self.telemetry: list[ExecutionTelemetry] = []

    def execute(self, request: AIRequest) -> AIResponse:
        attempts = 0
        last_error: Exception | None = None
        models = [self._model_for(request)]
        if request.policy.fallback_model and request.policy.fallback_model not in models:
            models.append(request.policy.fallback_model)
        for model in models:
            for _ in range(max(1, request.policy.max_retries + 1)):
                attempts += 1
                effective_policy = ModelPolicy(
                    name=request.policy.name,
                    reasoning_model=model if request.operation == "REASON" else request.policy.reasoning_model,
                    classification_model=model if request.operation == "CLASSIFY" else request.policy.classification_model,
                    extraction_model=model if request.operation == "EXTRACT" else request.policy.extraction_model,
                    max_retries=request.policy.max_retries,
                    fallback_model=request.policy.fallback_model,
                )
                effective_request = AIRequest(
                    operation=request.operation,
                    instruction=request.instruction,
                    input_data=request.input_data,
                    schema=request.schema,
                    categories=request.categories,
                    policy=effective_policy,
                )
                try:
                    response = self.gateway.execute(effective_request)
                    validate_output(response, effective_request)
                    response.attempts = attempts
                    self.telemetry.append(ExecutionTelemetry(
                        request.operation, response.model, response.latency_ms,
                        response.input_tokens, response.output_tokens, response.cost_usd,
                        attempts, True
                    ))
                    return response
                except Exception as exc:
                    last_error = exc
        raise CognitiveRuntimeError(f"Cognitive execution failed after {attempts} attempts: {last_error}")

    def _model_for(self, request: AIRequest) -> str:
        if request.operation == "CLASSIFY":
            return request.policy.classification_model
        if request.operation == "EXTRACT":
            return request.policy.extraction_model
        return request.policy.reasoning_model
