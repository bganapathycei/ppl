from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
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


class ExecutionStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    RESUMING = "RESUMING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


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

    def ready_nodes(self) -> list[GraphNode]:
        ready = []
        for node in self.nodes.values():
            if node.status is not NodeStatus.PENDING:
                continue
            if all(self.nodes[d].status is NodeStatus.SUCCEEDED for d in node.dependencies):
                ready.append(node)
        return ready

    def checkpoint(self, name: str) -> ExecutionCheckpoint:
        cp = ExecutionCheckpoint(
            checkpoint_id=name,
            execution_id=self.execution_id,
            completed_nodes=[n.node_id for n in self.nodes.values() if n.status is NodeStatus.SUCCEEDED],
            pending_nodes=[n.node_id for n in self.nodes.values() if n.status is NodeStatus.PENDING],
            context=dict(self.context),
        )
        self.checkpoints[name] = cp
        self.current_checkpoint_id = name
        self.status = ExecutionStatus.WAITING
        return cp

    def resume(self, checkpoint_id: str | None = None) -> None:
        checkpoint_id = checkpoint_id or self.current_checkpoint_id
        if not checkpoint_id or checkpoint_id not in self.checkpoints:
            raise KeyError("No valid checkpoint available")
        cp = self.checkpoints[checkpoint_id]
        self.context = dict(cp.context)
        for node in self.nodes.values():
            if node.node_id in cp.completed_nodes:
                node.status = NodeStatus.SUCCEEDED
            else:
                node.status = NodeStatus.PENDING
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
    def __init__(self) -> None:
        self.executions: dict[str, Execution] = {}

    def save(self, execution: Execution) -> None:
        self.executions[execution.execution_id] = execution

    def load(self, execution_id: str) -> Execution:
        if execution_id not in self.executions:
            raise KeyError(execution_id)
        return self.executions[execution_id]


class GraphExecutor:
    """Small async executor for graph scheduling, checkpointing and resume."""

    def __init__(self, store: InMemoryExecutionStore | None = None):
        self.store = store or InMemoryExecutionStore()

    async def run(
        self,
        execution: Execution,
        handlers: dict[str, Callable[[GraphNode, Execution], Any]],
    ) -> Execution:
        execution.status = ExecutionStatus.RUNNING
        self.store.save(execution)
        while True:
            if all(node.status is NodeStatus.SUCCEEDED for node in execution.nodes.values()):
                execution.status = ExecutionStatus.SUCCEEDED
                self.store.save(execution)
                return execution

            ready = execution.ready_nodes()
            if not ready:
                if any(node.status is NodeStatus.FAILED for node in execution.nodes.values()):
                    execution.status = ExecutionStatus.FAILED
                    self.store.save(execution)
                    return execution
                execution.status = ExecutionStatus.WAITING
                self.store.save(execution)
                return execution

            await asyncio.gather(*(self._execute_node(node, execution, handlers) for node in ready))
            self.store.save(execution)

    async def _execute_node(self, node: GraphNode, execution: Execution, handlers: dict[str, Callable]) -> None:
        node.status = NodeStatus.RUNNING
        try:
            result = handlers[node.operation](node, execution)
            if asyncio.iscoroutine(result):
                result = await result
            node.output = result
            node.status = NodeStatus.SUCCEEDED
            execution.context[node.node_id] = result
        except Exception as exc:  # noqa: BLE001
            node.error = str(exc)
            node.status = NodeStatus.FAILED

    def checkpoint(self, execution_id: str, name: str) -> ExecutionCheckpoint:
        execution = self.store.load(execution_id)
        cp = execution.checkpoint(name)
        self.store.save(execution)
        return cp

    async def resume(self, execution_id: str, handlers: dict[str, Callable], checkpoint_id: str | None = None) -> Execution:
        execution = self.store.load(execution_id)
        execution.resume(checkpoint_id)
        self.store.save(execution)
        return await self.run(execution, handlers)
