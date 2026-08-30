from dataclasses import dataclass, field
from typing import Any, Protocol
import time

@dataclass
class ModelPolicy:
    name: str = "default"
    reasoning_model: str = "reasoning-default"
    classification_model: str = "classification-default"
    extraction_model: str = "extraction-default"
    max_retries: int = 1
    fallback_model: str = "fallback-default"

@dataclass
class AIRequest:
    operation: str
    instruction: str
    input_data: Any
    schema: dict[str, str] = field(default_factory=dict)
    categories: list[str] = field(default_factory=list)
    policy: ModelPolicy = field(default_factory=ModelPolicy)

@dataclass
class AIResponse:
    output: dict[str, Any]
    model: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    attempts: int

class ModelAdapter(Protocol):
    def execute(self, request: AIRequest) -> AIResponse: ...

class LocalModelAdapter:
    """Deterministic adapter used by the reference runtime and tests."""
    def execute(self, request: AIRequest) -> AIResponse:
        start = time.perf_counter()
        text = str(request.input_data).lower()
        if request.operation == "CLASSIFY":
            scores = {c: 0 for c in request.categories}
            keywords = {
                "ACCESS": ["login", "password", "permission", "access", "authentication"],
                "NETWORK": ["network", "dns", "latency", "timeout"],
                "DATABASE": ["database", "db", "sql", "query", "connection pool", "deadlock"],
                "APPLICATION": ["application", "app", "crash", "exception"],
                "INFRASTRUCTURE": ["server", "cpu", "memory", "disk", "host"],
            }
            for category, words in keywords.items():
                if category in scores:
                    scores[category] = sum(1 for word in words if word in text)
            best = max(scores, key=scores.get)
            confidence = 0.55 if scores[best] == 0 else min(0.96, 0.70 + 0.08 * scores[best])
            output = {"category": best, "confidence": round(confidence, 2)}
        elif request.operation == "EXTRACT":
            output = {}
            if "root_cause" in request.schema:
                output["root_cause"] = "Database connection pool exhaustion" if "connection pool" in text else "Requires further investigation"
            if "resolution" in request.schema:
                output["resolution"] = "Restart or recycle the connection pool and validate database capacity" if "connection pool" in text else "Follow operational runbook"
        else:
            context = str(request.input_data).lower()
            if "repetitive" in request.instruction.lower():
                repetitive = any(x in context for x in ["repeated", "recurring", "again", "multiple", "historical"])
                output = {"repetitive": repetitive, "confidence": 0.88 if repetitive else 0.72}
            elif "automation" in request.instruction.lower() or "candidate" in request.instruction.lower():
                nested = request.input_data.get("context", request.input_data) if isinstance(request.input_data, dict) else {}
                repetitive = isinstance(nested, dict) and nested.get("repetitive") is True
                if not repetitive:
                    lowered = str(request.input_data).lower()
                    repetitive = "repetitive': true" in lowered or 'repetitive": true' in lowered
                output = {"score": 86 if repetitive else 42, "rationale": "Repetitive and relatively deterministic remediation." if repetitive else "Insufficient evidence of a repeatable remediation pattern.", "confidence": 0.89 if repetitive else 0.76}
            elif "safe" in request.instruction.lower():
                output = {
                    "safe": True,
                    "confidence": 0.92,
                    "rationale": "Change appears low risk and within policy.",
                }
            else:
                output = {"result": "REASONED", "confidence": 0.70}
        for field, typ in request.schema.items():
            if field in output:
                continue
            kind = typ.upper()
            if kind == "BOOLEAN":
                output[field] = bool(output.get("repetitive") or output.get("safe"))
            elif kind == "CONFIDENCE":
                output[field] = float(output.get("confidence", 0.7))
            elif kind in {"NUMBER", "INTEGER"}:
                output[field] = int(output.get("score", 0))
            elif kind == "CLASSIFICATION" and request.categories:
                output[field] = request.categories[0]
            else:
                output[field] = str(output.get("rationale") or output.get("root_cause") or "")
        latency = (time.perf_counter() - start) * 1000
        tokens = max(1, len(str(request.input_data).split()))
        return AIResponse(output, request.policy.reasoning_model, latency, tokens, max(1, len(str(output).split())), 0.001, 1)

class AIGateway:
    def __init__(self, adapter: ModelAdapter | None = None):
        self.adapter = adapter or LocalModelAdapter()

    def execute(self, request: AIRequest) -> AIResponse:
        response = self.adapter.execute(request)
        return response
