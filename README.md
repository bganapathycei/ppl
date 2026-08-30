# PPL — Prompt Programming Language

PPL is an experimental AI-native programming language for expressing deterministic computation, AI reasoning, knowledge, tools, workflows, human decisions, governance, and distributed execution as executable software.

> **The prompt is source code. The model is not the runtime.**

PPL source is parsed into an AST, compiled into a portable Prompt Intermediate Representation (PIR), lowered into an execution graph, and run by a provider-neutral runtime.

## Current version: 0.8 draft

PPL 0.8 adds execution-graph orchestration:

- explicit graph nodes and dependencies
- parallel branches
- joins and dependency barriers
- wait states
- checkpoints
- resume semantics
- graph-oriented execution state
- a path to distributed workers

Previous releases added:

- 0.2 — model abstraction and typed cognitive output
- 0.3 — knowledge, memory, tools, human decisions
- 0.4 — governance, authorization, budgets, evaluation, provenance
- 0.5 — developer experience and onboarding
- 0.6 — real AI provider adapters
- 0.7 — production-runtime foundations

## New developer? Start here

1. Read [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).
2. Run [`examples/hello_world.ppl`](examples/hello_world.ppl).
3. Study [`examples/incident.ppl`](examples/incident.ppl).
4. Study [`examples/governed_change.ppl`](examples/governed_change.ppl).
5. Read [`docs/TUTORIAL.md`](docs/TUTORIAL.md).
6. Read [`docs/SPEC.md`](docs/SPEC.md).
7. Study [`docs/PPL_0.8.md`](docs/PPL_0.8.md) and [`examples/execution_graph.py`](examples/execution_graph.py).

## Quick start

```bash
python -m pip install -e .
ppl check examples/hello_world.ppl
ppl compile examples/hello_world.ppl
ppl run examples/hello_world.ppl
ppl run examples/incident.ppl
ppl trace examples/incident.ppl
ppl run examples/governed_change.ppl
ppl fmt examples/hello_world.ppl
ppl test
```

The bundled local cognitive adapter remains deterministic for offline development. Real model execution is available through the provider-neutral AI runtime adapters.

## Architecture

```text
PPL Source
    |
    v
Lexer -> Parser -> AST -> Semantic Checks -> PIR
                                      |
                                      v
                             Execution Graph
                                      |
          +---------------------------+--------------------------+
          |                           |                          |
    Deterministic                 Cognitive                    Human
          |                           |                          |
       Rules/IF                 AI Gateway/Models          Approval/Review
          |                           |                          |
          +---------------------------+--------------------------+
                                      |
                       Knowledge / Memory / Tools
                                      |
                              State / Checkpoints
                                      |
                              Local / Workers
```

## Core language direction

```text
Intent
  -> typed program
  -> cognitive operations
  -> governed execution
  -> execution graph
  -> observable outcome
```

## Repository map

- `docs/GETTING_STARTED.md` — beginner onboarding
- `docs/TUTORIAL.md` — step-by-step tutorial
- `docs/EXAMPLES.md` — examples and learning path
- `docs/SPEC.md` — canonical language specification
- `docs/PPL_0.8.md` — execution-graph specification
- `docs/REAL_AI_RUNTIME.md` — real model setup
- `examples/` — language and runtime examples
- `src/ppl/` — reference implementation
- `tests/` — executable tests

## Status

PPL is experimental. The 0.x releases explore language semantics and runtime architecture. Syntax and runtime contracts may change before 1.0.
