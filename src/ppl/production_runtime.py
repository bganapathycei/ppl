"""PPL 0.7 production-runtime primitives.

Provider-neutral contracts for async execution, streaming events, typed
provider errors, retry/backoff decisions, durable execution state, and
model pricing. These primitives are deliberately adapter-oriented so they
can be replaced by real infrastructure without changing PPL source code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import asyncio
import random
import time
from typing import Any, AsyncIterator, Protocol


class RuntimeErrorCode(str, Enum):
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    TRANSIENT_ERROR = "TRANSIENT_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"


class PPLRuntimeError(Exception):
    def __init__(self, code: RuntimeErrorCode, message: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass
class StreamEvent:
    type: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionState:
    execution_id: str
    status: str = "RUNNING"
    step_index: int = 0
    context: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    result: Any = None
    error: dict[str, Any] | None = None


class ExecutionStore(Protocol):
    def create(self, state: ExecutionState) -> None: ...
    def read(self, execution_id: str) -> ExecutionState | None: ...
    def update(self, execution_id: str, **patch: Any) -> None: ...
    def append_event(self, execution_id: str, event: dict[str, Any]) -> None: ...


class InMemoryExecutionStore:
    def __init__(self) -> None:
        self._states: dict[str, ExecutionState] = {}

    def create(self, state: ExecutionState) -> None:
        if state.execution_id in self._states:
            raise ValueError(f"Execution already exists: {state.execution_id}")
        self._states[state.execution_id] = state

    def read(self, execution_id: str) -> ExecutionState | None:
        return self._states.get(execution_id)

    def update(self, execution_id: str, **patch: Any) -> None:
        state = self._states[execution_id]
        for key, value in patch.items():
            setattr(state, key, value)

    def append_event(self, execution_id: str, event: dict[str, Any]) -> None:
        self._states[execution_id].events.append(event)


@dataclass
class Pricing:
    input_per_million: float = 0.0
    output_per_million: float = 0.0

    def estimate(self, input_tokens: int, output_tokens: int) -> float:
        return round(
            (input_tokens / 1_000_000) * self.input_per_million
            + (output_tokens / 1_000_000) * self.output_per_million,
            8,
        )


@dataclass
class RuntimeExecutionResult:
    output: dict[str, Any]
    execution_id: str
    model: str
    latency_ms: float
    attempts: int
    cost_usd: float


class AsyncModelAdapter(Protocol):
    async def execute(self, request: Any) -> Any: ...

    async def stream(self, request: Any) -> AsyncIterator[StreamEvent]: ...


async def backoff(attempt: int, base_seconds: float = 0.5, max_seconds: float = 8.0) -> None:
    delay = min(max_seconds, base_seconds * (2 ** max(0, attempt - 1)))
    delay *= 0.5 + random.random()
    await asyncio.sleep(delay)


class ProductionExecutor:
    """Adapter-agnostic async execution wrapper with bounded retries."""

    def __init__(self, adapter: AsyncModelAdapter, store: ExecutionStore | None = None):
        self.adapter = adapter
        self.store = store or InMemoryExecutionStore()

    async def execute(self, request: Any, execution_id: str, max_retries: int = 1) -> Any:
        existing = self.store.read(execution_id)
        if existing is None:
            self.store.create(ExecutionState(execution_id=execution_id))
        started = time.perf_counter()
        attempts = 0
        while True:
            attempts += 1
            try:
                response = await self.adapter.execute(request)
                self.store.update(execution_id, status="COMPLETED")
                self.store.append_event(execution_id, {
                    "type": "COMPLETE",
                    "attempts": attempts,
                    "latency_ms": (time.perf_counter() - started) * 1000,
                })
                return response
            except PPLRuntimeError as exc:
                retryable = exc.retryable and attempts <= max_retries
                self.store.append_event(execution_id, {
                    "type": "ERROR",
                    "code": exc.code.value,
                    "attempt": attempts,
                    "retryable": retryable,
                })
                if not retryable:
                    self.store.update(execution_id, status="FAILED", error={"code": exc.code.value, "message": str(exc)})
                    raise
                await backoff(attempts)

    async def stream(self, request: Any, execution_id: str) -> AsyncIterator[StreamEvent]:
        existing = self.store.read(execution_id)
        if existing is None:
            self.store.create(ExecutionState(execution_id=execution_id))
        self.store.append_event(execution_id, {"type": "START"})
        try:
            async for event in self.adapter.stream(request):
                self.store.append_event(execution_id, {"type": event.type, "data": event.data})
                yield event
                if event.type == "COMPLETE":
                    self.store.update(execution_id, status="COMPLETED")
        except PPLRuntimeError as exc:
            self.store.update(execution_id, status="FAILED", error={"code": exc.code.value, "message": str(exc)})
            self.store.append_event(execution_id, {"type": "ERROR", "code": exc.code.value})
            raise
