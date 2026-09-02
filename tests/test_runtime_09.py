import json
import os
import time
from pathlib import Path

import pytest

from ppl.compiler import Compiler
from ppl.parser import parse
from ppl.runtime import Runtime, approve_execution
from ppl.store import FileExecutionStore, InMemoryGraphStore
from ppl.tools import build_tool_registry, resolve_action

ROOT = Path(__file__).resolve().parents[1]


def test_file_execution_store_roundtrip(tmp_path):
    store = FileExecutionStore(tmp_path)
    pir = Compiler().compile(parse((ROOT / "examples/hello_world.ppl").read_text(encoding="utf-8")))
    runtime = Runtime(pir, store=store, program_path=ROOT / "examples/hello_world.ppl", interactive=False)
    result = runtime.run({})
    assert result == "Hello, world"
    loaded = store.load(runtime.execution.execution_id)
    assert loaded.result == "Hello, world"
    assert loaded.status.value == "SUCCEEDED"


def test_knowledge_retrieval_changes_reason_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("PPL_KNOWLEDGE_DIR", str(ROOT / "examples" / "knowledge"))
    pir = Compiler().compile(parse((ROOT / "examples/enterprise_automation.ppl").read_text(encoding="utf-8")))
    runtime = Runtime(
        pir,
        store=InMemoryGraphStore(),
        program_path=ROOT / "examples/enterprise_automation.ppl",
        interactive=False,
    )
    result = runtime.run({
        "incident": {
            "id": "INC-1001",
            "description": "Repeated database connection pool failure",
            "application": "Order Management",
            "priority": "P2",
        }
    })
    assert result == "DATABASE"
    assert "knowledge" in runtime.context
    assert runtime.context["knowledge"]
    assert "connection pool" in str(runtime.context.get("Analyzer", {}).get("evidence", "")).lower() or \
        "pool" in str(runtime.context["knowledge"]).lower()


def test_memory_survives_second_run(tmp_path, monkeypatch):
    monkeypatch.setenv("PPL_MEMORY_DIR", str(tmp_path / "memory"))
    monkeypatch.setenv("PPL_KNOWLEDGE_DIR", str(ROOT / "examples" / "knowledge"))
    source = (ROOT / "examples/enterprise_automation.ppl").read_text(encoding="utf-8")
    pir = Compiler().compile(parse(source))
    first = Runtime(pir, store=InMemoryGraphStore(), program_path=ROOT / "examples/enterprise_automation.ppl", interactive=False)
    first.run({
        "incident": {
            "id": "INC-42",
            "description": "Repeated database connection pool failure",
            "application": "Order Management",
            "priority": "P2",
        }
    })
    mem_file = tmp_path / "memory" / "IncidentAutomation.json"
    assert mem_file.exists()
    data = json.loads(mem_file.read_text(encoding="utf-8"))
    assert "INC-42" in data

    second = Runtime(pir, store=InMemoryGraphStore(), program_path=ROOT / "examples/enterprise_automation.ppl", interactive=False)
    second.run({
        "incident": {
            "id": "INC-42",
            "description": "Repeated database connection pool failure",
            "application": "Order Management",
            "priority": "P2",
        }
    })
    assert second.context.get("memory") or "IncidentHistory" in str(second.context.get("Analyzer", {}).get("memory", second.context.get("memory")))


def test_call_unknown_action_raises():
    source = """
APP ToolFail
INPUT request
    text: TEXT
WORKFLOW Main
    RECEIVE request
    CALL MissingTool.unknown_action
    RETURN "NO"
"""
    pir = Compiler().compile(parse(source))
    runtime = Runtime(pir, store=InMemoryGraphStore(), interactive=False)
    runtime.run({"request": {"text": "x"}})
    assert runtime.execution is not None
    assert runtime.execution.status.value == "FAILED"
    assert any(n.status.value == "FAILED" for n in runtime.execution.nodes.values())


def test_workers_set_worker_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("PPL_WORKER_TIMEOUT", "15")
    from ppl.workers import run_with_workers
    from ppl.compiler import Compiler
    from ppl.parser import parse
    from ppl.store import FileExecutionStore

    program = ROOT / "examples" / "hello_world_ai.ppl"
    pir = Compiler().compile(parse(program.read_text(encoding="utf-8")))
    store = FileExecutionStore(tmp_path)
    result = run_with_workers(
        str(program),
        pir,
        {"request": {"text": "hello there"}},
        workers=2,
        store=store,
    )
    assert result in {"GREETING", "QUESTION", "OTHER"}
    # Find the saved execution
    ids = store.list_ids()
    assert ids
    execution = store.load(ids[0])
    workers = [n.metadata.get("worker") for n in execution.nodes.values() if n.metadata.get("worker")]
    assert workers
    assert any(w and w.startswith("worker-") for w in workers)


def test_human_pause_approve_resume(tmp_path, monkeypatch):
    monkeypatch.delenv("PPL_HUMAN_DECISION", raising=False)
    source = """
APP NeedsHuman
INPUT change
    description: TEXT
AGENT RiskAnalyzer
    INPUT change
    REASON
        determine whether the proposed change is safe
        OUTPUT:
            safe: BOOLEAN
            confidence: CONFIDENCE
            rationale: TEXT
    OUTPUT
        safe: BOOLEAN
        confidence: CONFIDENCE
WORKFLOW Main
    RECEIVE change
    RUN RiskAnalyzer
    HUMAN_APPROVAL
        QUESTION:
            approve the change
        OPTIONS:
            APPROVE
            REJECT
    RETURN "DONE"
"""
    pir = Compiler().compile(parse(source))
    store = FileExecutionStore(tmp_path)
    runtime = Runtime(pir, store=store, interactive=False)
    paused = runtime.run({"change": {"description": "touch production"}})
    assert paused["status"] == "WAITING"
    eid = paused["execution_id"]
    approve_execution(store, eid, "APPROVE")
    resumed = Runtime(pir, store=store, interactive=False).run(execution_id=eid, resume=True)
    assert resumed == "DONE"


def test_wait_file_predicate(tmp_path):
    marker = tmp_path / "paid"
    source = f"""
APP WaitFile
INPUT order
    id: TEXT
WORKFLOW Main
    RECEIVE order
    WAIT file:{marker.as_posix()}
    RETURN "PAID"
"""
    pir = Compiler().compile(parse(source))
    store = FileExecutionStore(tmp_path / "exec")
    runtime = Runtime(pir, store=store, interactive=False)
    paused = runtime.run({"order": {"id": "1"}})
    assert paused["status"] == "WAITING"
    eid = paused["execution_id"]
    still = Runtime(pir, store=store, interactive=False).run(execution_id=eid, resume=True)
    assert still["status"] == "WAITING"
    marker.write_text("1", encoding="utf-8")
    done = Runtime(pir, store=store, interactive=False).run(execution_id=eid, resume=True)
    assert done == "PAID"


def test_parallel_branches_overlap(monkeypatch):
    monkeypatch.setenv("PPL_PARALLEL_SLEEP", "0.05")
    source = """
APP ParallelTiming
INPUT request
    text: TEXT
AGENT Left
    INPUT request
    CLASSIFY request.text AS
        GREETING
        OTHER
    OUTPUT
        category
AGENT Right
    INPUT request
    CLASSIFY request.text AS
        QUESTION
        OTHER
    OUTPUT
        category
WORKFLOW Main
    RECEIVE request
    PARALLEL
        RUN Left
        RUN Right
    RETURN Left.category
"""
    pir = Compiler().compile(parse(source))
    started = time.perf_counter()
    result = Runtime(pir, store=InMemoryGraphStore(), interactive=False).run({"request": {"text": "hello"}})
    elapsed = time.perf_counter() - started
    assert result in {"GREETING", "OTHER"}
    # Sequential would be ~0.10s; overlapped gather should be closer to 0.05-0.08
    assert elapsed < 0.09


def test_tool_registry_fail_closed():
    registry = build_tool_registry([])
    assert resolve_action("ServiceManagement.create_ticket") == "create_ticket"
    with pytest.raises(KeyError):
        registry.call("definitely_missing")
