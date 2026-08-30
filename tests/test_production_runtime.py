import pytest

from ppl.production_runtime import (
    AsyncModelAdapter,
    InMemoryExecutionStore,
    PPLRuntimeError,
    ProductionExecutor,
    RuntimeErrorCode,
    StreamEvent,
)


class FakeAdapter:
    def __init__(self):
        self.calls = 0

    async def execute(self, request):
        self.calls += 1
        if self.calls == 1:
            raise PPLRuntimeError(RuntimeErrorCode.RATE_LIMIT_ERROR, "retry", retryable=True)
        return {"ok": True}

    async def stream(self, request):
        yield StreamEvent("DELTA", {"text": "hello"})
        yield StreamEvent("COMPLETE", {"ok": True})


@pytest.mark.asyncio
async def test_retry_and_persisted_state(monkeypatch):
    async def no_sleep(*args, **kwargs):
        return None

    monkeypatch.setattr("ppl.production_runtime.backoff", no_sleep)
    store = InMemoryExecutionStore()
    adapter = FakeAdapter()
    executor = ProductionExecutor(adapter, store)

    result = await executor.execute({}, "exec-1", max_retries=1)

    assert result == {"ok": True}
    assert adapter.calls == 2
    assert store.read("exec-1").status == "COMPLETED"
    assert any(e["type"] == "ERROR" for e in store.read("exec-1").events)


@pytest.mark.asyncio
async def test_streaming_events_are_persisted():
    store = InMemoryExecutionStore()
    executor = ProductionExecutor(FakeAdapter(), store)
    events = [event async for event in executor.stream({}, "exec-stream")]

    assert [e.type for e in events] == ["DELTA", "COMPLETE"]
    assert store.read("exec-stream").status == "COMPLETED"
