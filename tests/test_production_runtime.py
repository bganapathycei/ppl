import asyncio

from ppl.production_runtime import (
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


def test_retry_and_persisted_state(monkeypatch):
    async def no_sleep(*args, **kwargs):
        return None

    monkeypatch.setattr("ppl.production_runtime.backoff", no_sleep)
    store = InMemoryExecutionStore()
    adapter = FakeAdapter()
    executor = ProductionExecutor(adapter, store)

    async def run():
        return await executor.execute({}, "exec-1", max_retries=1)

    result = asyncio.run(run())
    assert result == {"ok": True}
    assert adapter.calls == 2
    assert store.read("exec-1").status == "COMPLETED"
    assert any(event["type"] == "ERROR" for event in store.read("exec-1").events)


def test_streaming_events_are_persisted():
    store = InMemoryExecutionStore()
    executor = ProductionExecutor(FakeAdapter(), store)

    async def run():
        return [event async for event in executor.stream({}, "exec-stream")]

    events = asyncio.run(run())
    assert [event.type for event in events] == ["DELTA", "COMPLETE"]
    assert store.read("exec-stream").status == "COMPLETED"
