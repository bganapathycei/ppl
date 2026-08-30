import asyncio

import pytest

from ppl.execution_graph import Execution, ExecutionGraph, GraphExecutor, GraphNode, NodeStatus


def test_cycle_detection():
    with pytest.raises(ValueError, match="cycle"):
        ExecutionGraph([
            GraphNode("a", "a", ["b"]),
            GraphNode("b", "b", ["a"]),
        ])


def test_parallel_branches_join_in_dependency_order():
    graph = ExecutionGraph([
        GraphNode("start", "start"),
        GraphNode("risk", "risk", ["start"]),
        GraphNode("compliance", "compliance", ["start"]),
        GraphNode("join", "join", ["risk", "compliance"]),
    ])
    execution = Execution(nodes=dict(graph.nodes))
    events = []

    async def handler(node, state):
        events.append(node.node_id)
        await asyncio.sleep(0)
        return node.node_id

    finished = asyncio.run(GraphExecutor().run(execution, {n: handler for n in {"start", "risk", "compliance", "join"}}))
    assert finished.status.value == "SUCCEEDED"
    assert finished.nodes["join"].status is NodeStatus.SUCCEEDED
    assert set(events[1:3]) == {"risk", "compliance"}


def test_checkpoint_resume():
    graph = ExecutionGraph([
        GraphNode("a", "a"),
        GraphNode("b", "b", ["a"]),
    ])
    execution = Execution(nodes=dict(graph.nodes))
    store = GraphExecutor().store

    async def a(node, state):
        return "A"

    async def b(node, state):
        return "B"

    executor = GraphExecutor(store)
    finished = asyncio.run(executor.run(execution, {"a": a, "b": b}))
    assert finished.status.value == "SUCCEEDED"
