import asyncio

from ppl.execution_graph import Execution, ExecutionGraph, GraphExecutor, GraphNode


def make_graph():
    nodes = [
        GraphNode("receive", "receive"),
        GraphNode("risk", "risk", ["receive"]),
        GraphNode("compliance", "compliance", ["receive"]),
        GraphNode("join", "join", ["risk", "compliance"]),
        GraphNode("decision", "decision", ["join"]),
    ]
    return ExecutionGraph(nodes)


async def main():
    graph = make_graph()
    execution = Execution(nodes=dict(graph.nodes)).nodes
    run = Execution(nodes=execution)

    async def receive(node, state):
        return "received"

    async def risk(node, state):
        await asyncio.sleep(0.01)
        return "low-risk"

    async def compliance(node, state):
        await asyncio.sleep(0.01)
        return "compliant"

    async def join(node, state):
        return "joined"

    async def decision(node, state):
        return "approved"

    handlers = {
        "receive": receive,
        "risk": risk,
        "compliance": compliance,
        "join": join,
        "decision": decision,
    }

    executor = GraphExecutor()
    finished = await executor.run(run, handlers)
    print(finished.status.value)
    print(finished.context)


if __name__ == "__main__":
    asyncio.run(main())
