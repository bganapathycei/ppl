# PPL 0.8 — Execution Graph & Distributed Orchestration

> Historical note for **0.8** (graph *specification*). Current release is **0.10**. The graph became a durable local runtime in [PPL_0.9.md](PPL_0.9.md).

PPL 0.8 defines an execution-graph layer above the existing deterministic, cognitive, tool, knowledge, memory, and human primitives.

## Goals

- represent workflows as explicit execution graphs
- support parallel branches
- join dependent branches
- wait on external conditions or time
- checkpoint execution state
- resume from a checkpoint
- inspect the compiled execution graph
- provide a path to distributed workers without changing PPL source

## New concepts

### GRAPH

A workflow is compiled into a directed execution graph. Every executable node receives a stable node ID.

### PARALLEL

Runs independent branches concurrently.

```text
PARALLEL
    RUN RiskAnalyzer
    RUN ComplianceAnalyzer
```

### JOIN

Waits until named parallel branches complete.

```text
JOIN RiskAnalyzer
JOIN ComplianceAnalyzer
```

### WAIT

Suspends execution until a runtime condition, event, or duration is satisfied.

```text
WAIT order.payment_received
```

### CHECKPOINT

Persists the current execution state and graph position.

```text
CHECKPOINT after_analysis
```

### RESUME

The runtime may resume an interrupted execution from the latest valid checkpoint.

## Execution state

A production execution should contain:

```text
execution_id
program_version
workflow_name
graph_version
current_nodes
completed_nodes
failed_nodes
context
checkpoint_id
status
created_at
updated_at
```

Recommended statuses:

```text
CREATED
RUNNING
WAITING
CHECKPOINTED
RESUMING
SUCCEEDED
FAILED
CANCELLED
```

## Distributed model

The language stays provider-neutral and infrastructure-neutral:

```text
PPL -> PIR -> Execution Graph
                      |
             +--------+--------+
             |        |        |
           Worker   Worker   Worker
             |        |        |
             +--------+--------+
                      |
                 State Store
```

The runtime decides whether a graph node executes in-process, in a worker process, or on a remote worker.

## Graph determinism

Node identifiers, input dependencies, and state transitions SHOULD be stable enough to replay or resume executions. Side-effecting nodes SHOULD declare idempotency requirements.

## Checkpoint semantics

A checkpoint is a durable snapshot of:

- execution state
- application context
- completed node outputs
- pending nodes
- graph position
- relevant runtime metadata

A resume operation MUST NOT silently rerun a completed non-idempotent side effect.

## Failure semantics

A graph node may fail independently. The runtime should support:

- node retry
- branch retry
- compensation hooks in later versions
- checkpoint recovery
- explicit terminal failure

## Observability

Execution traces should expose the graph structure:

```text
A Receive
  |
  +--> B RiskAnalyzer ----+
  |                        |
  +--> C Compliance -------+--> D Join --> E Decision
```

## Non-goals for 0.8

- production distributed scheduler
- exactly-once external side effects
- global transactional semantics
- automatic compensation planning

Those are 0.9+ concerns. Local durable interpretation and a process-pool worker shipped in 0.9; a remote distributed scheduler is still out of scope.
