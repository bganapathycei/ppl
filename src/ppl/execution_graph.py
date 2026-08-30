from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol
import asyncio
import time
import uuid


class NodeStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    WAITING = "WAITING"
    CHECKPOINTED = "CHECKPOINTED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


class ExecutionStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    RESUMING = "RESUMING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PauseExecution(Exception):
    """Signal that the graph should stop in WAITING until resumed."""

    def __init__(self, wait: dict[str, Any]):
        super().__init__(wait.get("reason", "waiting"))
        self.wait = wait


@dataclass
class GraphNode:
    node_id: str
    operation: str
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: NodeStatus = NodeStatus.PENDING
    output: Any = None
    error: str | None = None


@dataclass
class ExecutionCheckpoint:
    checkpoint_id: str
    execution_id: str
    completed_nodes: list[str]
    pending_nodes: list[str]
    context: dict[str, Any]
    created_at: float = field(default_factory=time.time)


@dataclass
class Execution:
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ExecutionStatus = ExecutionStatus.CREATED
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    checkpoints: dict[str, ExecutionCheckpoint] = field(default_factory=dict)
    current_checkpoint_id: str | None = None
    program_path: str | None = None
    graph_version: str = "0.9"
    result: Any = None
    wait: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def ready_nodes(self) -> list[GraphNode]:
        ready = []
        for node in self.nodes.values():
            if node.status is not NodeStatus.PENDING:
                continue
            if self._branch_skipped(node):
                node.status = NodeStatus.SKIPPED
                continue
            if all(
                self.nodes[d].status in {NodeStatus.SUCCEEDED, NodeStatus.SKIPPED, NodeStatus.CHECKPOINTED}
                for d in node.dependencies
            ):
                ready.append(node)
        return ready

    def _branch_skipped(self, node: GraphNode) -> bool:
        gate = node.metadata.get("gate")
        branch = node.metadata.get("branch")
        if not gate or not branch:
            return False
        gates = self.context.get("_gates") or {}
        taken = gates.get(gate)
        return taken is not None and taken != branch

    def checkpoint(self, name: str) -> ExecutionCheckpoint:
        cp = ExecutionCheckpoint(
            checkpoint_id=name,
            execution_id=self.execution_id,
            completed_nodes=[
                n.node_id
                for n in self.nodes.values()
                if n.status in {NodeStatus.SUCCEEDED, NodeStatus.SKIPPED, NodeStatus.CHECKPOINTED}
            ],
            pending_nodes=[n.node_id for n in self.nodes.values() if n.status is NodeStatus.PENDING],
            context=dict(self.context),
        )
        self.checkpoints[name] = cp
        self.current_checkpoint_id = name
        return cp

    def resume_from_wait(self) -> None:
        """Clear wait state and re-queue WAITING nodes as PENDING."""
        self.wait = None
        for node in self.nodes.values():
            if node.status is NodeStatus.WAITING:
                node.status = NodeStatus.PENDING
        self.status = ExecutionStatus.RESUMING

    def resume(self, checkpoint_id: str | None = None) -> None:
        checkpoint_id = checkpoint_id or self.current_checkpoint_id
        if not checkpoint_id or checkpoint_id not in self.checkpoints:
            raise KeyError("No valid checkpoint available")
        cp = self.checkpoints[checkpoint_id]
        self.context = dict(cp.context)
        for node in self.nodes.values():
            if node.node_id in cp.completed_nodes:
                if node.status not in {NodeStatus.SUCCEEDED, NodeStatus.SKIPPED, NodeStatus.CHECKPOINTED}:
                    node.status = NodeStatus.SUCCEEDED
            elif node.status is not NodeStatus.SKIPPED:
                node.status = NodeStatus.PENDING
        self.wait = None
        self.status = ExecutionStatus.RESUMING


class ExecutionGraph:
    def __init__(self, nodes: list[GraphNode]):
        self.nodes = {node.node_id: node for node in nodes}
        self._validate()

    def _validate(self) -> None:
        for node in self.nodes.values():
            for dependency in node.dependencies:
                if dependency not in self.nodes:
                    raise ValueError(f"Unknown dependency: {dependency}")
        self.topological_order()

    def topological_order(self) -> list[str]:
        indegree = {node_id: 0 for node_id in self.nodes}
        children = {node_id: [] for node_id in self.nodes}
        for node in self.nodes.values():
            indegree[node.node_id] = len(node.dependencies)
            for dep in node.dependencies:
                children[dep].append(node.node_id)
        queue = [n for n, degree in indegree.items() if degree == 0]
        order: list[str] = []
        while queue:
            current = queue.pop(0)
            order.append(current)
            for child in children[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if len(order) != len(self.nodes):
            raise ValueError("Execution graph contains a cycle")
        return order


class InMemoryExecutionStore:
    """Legacy alias used by examples/tests; prefer store.InMemoryGraphStore."""

    def __init__(self) -> None:
        self.executions: dict[str, Execution] = {}

    def save(self, execution: Execution) -> None:
        self.executions[execution.execution_id] = execution

    def load(self, execution_id: str) -> Execution:
        if execution_id not in self.executions:
            raise KeyError(execution_id)
        return self.executions[execution_id]


class GraphStoreProtocol(Protocol):
    def save(self, execution: Execution) -> None: ...
    def load(self, execution_id: str) -> Execution: ...


class GraphExecutor:
    """Async executor for graph scheduling, pause/wait, checkpoint and resume."""

    def __init__(self, store: GraphStoreProtocol | None = None, worker_id: str | None = None):
        self.store = store or InMemoryExecutionStore()
        self.worker_id = worker_id

    async def run(
        self,
        execution: Execution,
        handlers: dict[str, Callable[[GraphNode, Execution], Any]],
    ) -> Execution:
        execution.status = ExecutionStatus.RUNNING
        self.store.save(execution)
        while True:
            terminal = {NodeStatus.SUCCEEDED, NodeStatus.SKIPPED, NodeStatus.CHECKPOINTED, NodeStatus.CANCELLED}
            if all(node.status in terminal for node in execution.nodes.values()):
                execution.status = ExecutionStatus.SUCCEEDED
                execution.wait = None
                self.store.save(execution)
                return execution

            if execution.result is not None and not any(
                n.status is NodeStatus.PENDING for n in execution.nodes.values()
            ):
                for node in execution.nodes.values():
                    if node.status is NodeStatus.PENDING:
                        node.status = NodeStatus.CANCELLED
                execution.status = ExecutionStatus.SUCCEEDED
                execution.wait = None
                self.store.save(execution)
                return execution

            ready = execution.ready_nodes()
            if not ready:
                if any(node.status is NodeStatus.FAILED for node in execution.nodes.values()):
                    execution.status = ExecutionStatus.FAILED
                    self.store.save(execution)
                    return execution
                if any(node.status is NodeStatus.WAITING for node in execution.nodes.values()):
                    execution.status = ExecutionStatus.WAITING
                    self.store.save(execution)
                    return execution
                # Mark remaining unreachable pending as skipped after branch cancel
                pending = [n for n in execution.nodes.values() if n.status is NodeStatus.PENDING]
                if pending:
                    for n in pending:
                        if execution._branch_skipped(n):
                            n.status = NodeStatus.SKIPPED
                    continue
                execution.status = ExecutionStatus.WAITING
                self.store.save(execution)
                return execution

            try:
                await asyncio.gather(*(self._execute_node(node, execution, handlers) for node in ready))
            except PauseExecution as pause:
                execution.wait = pause.wait
                execution.status = ExecutionStatus.WAITING
                self.store.save(execution)
                return execution
            self.store.save(execution)
            if execution.result is not None:
                for node in execution.nodes.values():
                    if node.status is NodeStatus.PENDING:
                        node.status = NodeStatus.CANCELLED
                execution.status = ExecutionStatus.SUCCEEDED
                self.store.save(execution)
                return execution

    async def _execute_node(self, node: GraphNode, execution: Execution, handlers: dict[str, Callable]) -> None:
        if execution._branch_skipped(node):
            node.status = NodeStatus.SKIPPED
            return
        node.status = NodeStatus.RUNNING
        if self.worker_id:
            node.metadata["worker"] = self.worker_id
        try:
            handler = handlers.get(node.operation) or handlers.get("*")
            if handler is None:
                raise KeyError(f"No handler for operation {node.operation}")
            # Run sync handlers in a worker thread so PARALLEL branches overlap.
            result = await asyncio.to_thread(handler, node, execution)
            if asyncio.iscoroutine(result):
                result = await result
            if node.status is NodeStatus.WAITING:
                raise PauseExecution(execution.wait or {"reason": node.operation, "node_id": node.node_id})
            node.output = result
            if node.status is not NodeStatus.CHECKPOINTED:
                node.status = NodeStatus.SUCCEEDED
            execution.context[node.node_id] = result
            execution.events.append({
                "type": "NODE_COMPLETE",
                "node_id": node.node_id,
                "operation": node.operation,
                "worker": node.metadata.get("worker"),
                "ts": time.time(),
            })
        except PauseExecution:
            node.status = NodeStatus.WAITING
            raise
        except Exception as exc:  # noqa: BLE001
            node.error = str(exc)
            node.status = NodeStatus.FAILED
            execution.events.append({
                "type": "NODE_FAILED",
                "node_id": node.node_id,
                "error": str(exc),
                "ts": time.time(),
            })

    def checkpoint(self, execution_id: str, name: str) -> ExecutionCheckpoint:
        execution = self.store.load(execution_id)
        cp = execution.checkpoint(name)
        self.store.save(execution)
        return cp

    async def resume(
        self,
        execution_id: str,
        handlers: dict[str, Callable],
        checkpoint_id: str | None = None,
    ) -> Execution:
        execution = self.store.load(execution_id)
        if checkpoint_id:
            execution.resume(checkpoint_id)
        else:
            execution.resume_from_wait()
        self.store.save(execution)
        return await self.run(execution, handlers)
