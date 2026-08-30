# PPL Language Specification — Draft 0.9

## 1. Purpose

PPL (Prompt Programming Language) is an AI-native, intent-oriented programming language. A PPL application expresses data, deterministic control flow, cognitive operations, enterprise knowledge, memory, tools, human decisions, governance, evaluation, and graph orchestration without embedding a model-provider API in application source.

As of 0.9, the reference runtime executes the compiled graph with durable local state, file-backed knowledge/memory, fail-closed tools, human pause/resume, WAIT predicates, overlapping PARALLEL branches, and an optional single-machine worker pool. Remote distributed workers remain a future concern.


## 2. Execution classes

- **D — Deterministic:** parsing, branching, data movement, validation, arithmetic, state transitions, orchestration, and ordinary control.
- **C — Cognitive:** classification, extraction, reasoning, planning, generation, and other model-backed operations.
- **H — Human:** approval, review, escalation, correction, and other human-in-the-loop operations.

## 3. Compilation model

```text
Source -> AST -> Semantic Validation -> PIR -> Execution Graph -> Runtime
```

The runtime may execute graph nodes locally or on remote workers without changing PPL source.

## 4. Execution graph

Every workflow compiles to a directed execution graph. Each node has a stable node ID, operation type, dependencies, runtime status, output, and error state.

```text
A Receive
  |
  +--> B RiskAnalyzer -----+
  |                        |
  +--> C Compliance -------+--> D Join --> E Decision
```

The graph MUST be acyclic.

## 5. Parallel execution

`PARALLEL` expresses independent work that may run concurrently.

```text
PARALLEL
    RUN RiskAnalyzer
    RUN ComplianceAnalyzer
```

The runtime may schedule these nodes on separate workers when available.

## 6. JOIN

`JOIN` represents an explicit dependency barrier. A dependent node can execute only after all joined branches succeed.

## 7. WAIT

`WAIT` suspends the graph while an external event, condition, or duration is unresolved. The runtime status becomes `WAITING`.

## 8. CHECKPOINT and RESUME

A checkpoint persists enough state to resume execution safely:

- execution ID
- graph version
- completed nodes
- pending nodes
- application context
- checkpoint ID
- relevant runtime metadata

A resumed execution MUST restore completed-node state and MUST NOT silently rerun completed non-idempotent side effects.

## 9. Distributed execution

The graph abstraction is infrastructure-neutral:

```text
PPL -> PIR -> Execution Graph
                  |
          +-------+-------+
          |       |       |
        Worker  Worker  Worker
          |       |       |
          +-------+-------+
                  |
             State Store
```

Workers are an implementation detail of the runtime.

## 10. Node failure

A graph node may fail independently. The runtime SHOULD support node-level retry and preserve failure metadata. Future releases may add compensation and transactional semantics.

## 11. Runtime states

Execution state includes:

```text
CREATED
RUNNING
WAITING
RESUMING
SUCCEEDED
FAILED
CANCELLED
```

Node state includes:

```text
PENDING
RUNNING
SUCCEEDED
FAILED
WAITING
CHECKPOINTED
CANCELLED
```

## 12. Governance

`GUARD`, `AUTHORIZATION`, `ENVIRONMENT`, and `BUDGET` remain runtime-enforced controls. Governance applies to graph nodes as well as direct operations.

## 13. Cognitive execution

Cognitive nodes continue to use the provider-neutral AI request/response contract. Cognitive outputs MUST be schema-validated before entering program state. Model selection, retries, fallback, and telemetry remain runtime responsibilities.

## 14. Human execution

Human approval is a graph state transition:

```text
RUNNING -> WAITING -> RESUMING -> RUNNING
```

The decision is attributable to execution ID, actor, timestamp, question, options, and value.

## 15. Observability

Graph traces SHOULD expose:

- graph version
- node ID
- operation
- dependencies
- execution worker
- model/provider for cognitive nodes
- latency
- tokens
- cost
- retries
- checkpoints
- human decisions
- final state

## 16. Design principles

1. Intent over provider API.
2. Deterministic shell around cognitive operations.
3. Cognitive outputs are typed data.
4. Knowledge, memory, tools, humans, and orchestration are first-class concepts.
5. Governance is enforced by the runtime.
6. Evaluation is part of programming.
7. Execution is observable and attributable.
8. Graph orchestration is portable across local and distributed runtimes.
