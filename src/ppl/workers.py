"""Local single-machine worker pool for PPL 0.9.

Uses multiprocessing and a shared FileExecutionStore. This is a process pool,
not a distributed cluster.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import time
import uuid
from pathlib import Path
from typing import Any

from .ai_gateway import AIGateway
from .compiler import Compiler
from .execution_graph import ExecutionStatus, NodeStatus, PauseExecution
from .parser import parse
from .provider import build_adapter
from .runtime import Runtime
from .store import FileExecutionStore


def _worker_loop(store_dir: str, program_path: str, worker_name: str, stop_event: Any) -> None:
    store = FileExecutionStore(store_dir)
    source = Path(program_path).read_text(encoding="utf-8")
    pir = Compiler().compile(parse(source))
    gateway = AIGateway(build_adapter())
    while not stop_event.is_set():
        claimed = False
        for execution_id in store.list_ids():
            try:
                execution = store.load(execution_id)
            except KeyError:
                continue
            if execution.status not in {ExecutionStatus.RUNNING, ExecutionStatus.CREATED, ExecutionStatus.RESUMING}:
                continue
            ready = [
                n for n in execution.nodes.values()
                if n.status is NodeStatus.PENDING
                and all(
                    execution.nodes[d].status in {NodeStatus.SUCCEEDED, NodeStatus.SKIPPED, NodeStatus.CHECKPOINTED}
                    for d in n.dependencies
                )
                and not execution._branch_skipped(n)
            ]
            if not ready:
                continue
            node = ready[0]
            node.status = NodeStatus.RUNNING
            node.metadata["worker"] = worker_name
            store.save(execution)
            runtime = Runtime(pir, gateway=gateway, store=store, program_path=program_path, worker_id=worker_name)
            runtime.execution = execution
            runtime.context = execution.context
            try:
                handlers = runtime._handlers()
                handler = handlers.get(node.operation)
                if handler is None:
                    raise KeyError(node.operation)
                result = handler(node, execution)
                if node.status is NodeStatus.WAITING:
                    execution.status = ExecutionStatus.WAITING
                else:
                    node.output = result
                    if node.status is not NodeStatus.CHECKPOINTED:
                        node.status = NodeStatus.SUCCEEDED
                    execution.context[node.node_id] = result
                    if execution.result is not None:
                        for other in execution.nodes.values():
                            if other.status is NodeStatus.PENDING:
                                other.status = NodeStatus.CANCELLED
                        execution.status = ExecutionStatus.SUCCEEDED
            except PauseExecution as pause:
                execution.status = ExecutionStatus.WAITING
                execution.wait = pause.wait
                node.status = NodeStatus.WAITING
            except Exception as exc:  # noqa: BLE001
                node.error = str(exc)
                node.status = NodeStatus.FAILED
                execution.status = ExecutionStatus.FAILED
            store.save(execution)
            claimed = True
            break
        if not claimed:
            time.sleep(0.05)


def run_with_workers(
    program_path: str,
    pir: dict[str, Any],
    input_data: dict[str, Any],
    workers: int,
    store: FileExecutionStore | None = None,
    execution_id: str | None = None,
) -> Any:
    """Spawn N worker processes and drive execution via the shared store."""
    store = store or FileExecutionStore()
    runtime = Runtime(pir, gateway=AIGateway(build_adapter()), store=store, program_path=program_path)
    execution = runtime._new_execution(input_data, execution_id)
    execution.status = ExecutionStatus.RUNNING
    store.save(execution)

    ctx = mp.get_context("spawn")
    stop = ctx.Event()
    procs = []
    for i in range(max(1, workers)):
        name = f"worker-{i+1}-{uuid.uuid4().hex[:4]}"
        proc = ctx.Process(
            target=_worker_loop,
            args=(str(store.root), str(program_path), name, stop),
            daemon=True,
        )
        proc.start()
        procs.append(proc)

    try:
        deadline = time.time() + float(os.getenv("PPL_WORKER_TIMEOUT", "30"))
        while time.time() < deadline:
            execution = store.load(execution.execution_id)
            if execution.status in {ExecutionStatus.SUCCEEDED, ExecutionStatus.FAILED, ExecutionStatus.WAITING}:
                break
            # Also finish if all nodes terminal
            terminal = {NodeStatus.SUCCEEDED, NodeStatus.SKIPPED, NodeStatus.CHECKPOINTED, NodeStatus.CANCELLED, NodeStatus.FAILED}
            if execution.nodes and all(n.status in terminal for n in execution.nodes.values()):
                execution.status = ExecutionStatus.SUCCEEDED
                store.save(execution)
                break
            time.sleep(0.05)
        execution = store.load(execution.execution_id)
        # Attach a lightweight runtime for trace/result access
        runtime.execution = execution
        runtime.context = execution.context
        runtime.return_value = execution.result
        if execution.status is ExecutionStatus.WAITING:
            return {
                "status": "WAITING",
                "execution_id": execution.execution_id,
                "wait": execution.wait,
            }
        return execution.result if execution.result is not None else execution.context
    finally:
        stop.set()
        for proc in procs:
            proc.join(timeout=1)
            if proc.is_alive():
                proc.terminate()
