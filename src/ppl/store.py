"""Durable execution store for PPL 0.9.

FileExecutionStore persists graph executions as JSON under
`.ppl/executions/<execution_id>.json` (override with PPL_STATE_DIR).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Protocol

from .execution_graph import (
    Execution,
    ExecutionCheckpoint,
    ExecutionStatus,
    GraphNode,
    NodeStatus,
)


def default_state_dir() -> Path:
    override = os.getenv("PPL_STATE_DIR")
    if override:
        return Path(override)
    return Path.cwd() / ".ppl" / "executions"


class GraphStore(Protocol):
    def save(self, execution: Execution) -> None: ...
    def load(self, execution_id: str) -> Execution: ...
    def exists(self, execution_id: str) -> bool: ...
    def list_ids(self) -> list[str]: ...


def _node_to_dict(node: GraphNode) -> dict[str, Any]:
    return {
        "node_id": node.node_id,
        "operation": node.operation,
        "dependencies": list(node.dependencies),
        "metadata": node.metadata,
        "status": node.status.value,
        "output": node.output,
        "error": node.error,
    }


def _node_from_dict(data: dict[str, Any]) -> GraphNode:
    return GraphNode(
        node_id=data["node_id"],
        operation=data["operation"],
        dependencies=list(data.get("dependencies") or []),
        metadata=dict(data.get("metadata") or {}),
        status=NodeStatus(data.get("status", "PENDING")),
        output=data.get("output"),
        error=data.get("error"),
    )


def _checkpoint_to_dict(cp: ExecutionCheckpoint) -> dict[str, Any]:
    return {
        "checkpoint_id": cp.checkpoint_id,
        "execution_id": cp.execution_id,
        "completed_nodes": list(cp.completed_nodes),
        "pending_nodes": list(cp.pending_nodes),
        "context": cp.context,
        "created_at": cp.created_at,
    }


def _checkpoint_from_dict(data: dict[str, Any]) -> ExecutionCheckpoint:
    return ExecutionCheckpoint(
        checkpoint_id=data["checkpoint_id"],
        execution_id=data["execution_id"],
        completed_nodes=list(data.get("completed_nodes") or []),
        pending_nodes=list(data.get("pending_nodes") or []),
        context=dict(data.get("context") or {}),
        created_at=float(data.get("created_at") or time.time()),
    )


def execution_to_dict(execution: Execution) -> dict[str, Any]:
    return {
        "execution_id": execution.execution_id,
        "status": execution.status.value,
        "nodes": {nid: _node_to_dict(n) for nid, n in execution.nodes.items()},
        "context": execution.context,
        "checkpoints": {cid: _checkpoint_to_dict(cp) for cid, cp in execution.checkpoints.items()},
        "current_checkpoint_id": execution.current_checkpoint_id,
        "program_path": execution.program_path,
        "graph_version": execution.graph_version,
        "result": execution.result,
        "wait": execution.wait,
        "events": list(execution.events),
        "updated_at": time.time(),
    }


def execution_from_dict(data: dict[str, Any]) -> Execution:
    nodes = {nid: _node_from_dict(nd) for nid, nd in (data.get("nodes") or {}).items()}
    checkpoints = {
        cid: _checkpoint_from_dict(cp) for cid, cp in (data.get("checkpoints") or {}).items()
    }
    return Execution(
        execution_id=data["execution_id"],
        status=ExecutionStatus(data.get("status", "CREATED")),
        nodes=nodes,
        context=dict(data.get("context") or {}),
        checkpoints=checkpoints,
        current_checkpoint_id=data.get("current_checkpoint_id"),
        program_path=data.get("program_path"),
        graph_version=data.get("graph_version", "0.9"),
        result=data.get("result"),
        wait=data.get("wait"),
        events=list(data.get("events") or []),
    )


class InMemoryGraphStore:
    def __init__(self) -> None:
        self.executions: dict[str, Execution] = {}

    def save(self, execution: Execution) -> None:
        self.executions[execution.execution_id] = execution

    def load(self, execution_id: str) -> Execution:
        if execution_id not in self.executions:
            raise KeyError(execution_id)
        return self.executions[execution_id]

    def exists(self, execution_id: str) -> bool:
        return execution_id in self.executions

    def list_ids(self) -> list[str]:
        return sorted(self.executions)


class FileExecutionStore:
    """JSON-backed durable store with a simple lock file per execution."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root else default_state_dir()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, execution_id: str) -> Path:
        safe = execution_id.replace("/", "_").replace("\\", "_")
        return self.root / f"{safe}.json"

    def _lock_path(self, execution_id: str) -> Path:
        return self._path(execution_id).with_suffix(".lock")

    def save(self, execution: Execution) -> None:
        path = self._path(execution.execution_id)
        lock = self._lock_path(execution.execution_id)
        lock.write_text(str(os.getpid()), encoding="utf-8")
        try:
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(execution_to_dict(execution), indent=2), encoding="utf-8")
            tmp.replace(path)
        finally:
            if lock.exists():
                lock.unlink(missing_ok=True)

    def load(self, execution_id: str) -> Execution:
        path = self._path(execution_id)
        if not path.exists():
            raise KeyError(execution_id)
        return execution_from_dict(json.loads(path.read_text(encoding="utf-8")))

    def exists(self, execution_id: str) -> bool:
        return self._path(execution_id).exists()

    def list_ids(self) -> list[str]:
        return sorted(p.stem for p in self.root.glob("*.json"))
