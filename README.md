# PPL — Prompt Programming Language

PPL is an experimental AI-native programming language for expressing deterministic computation, AI reasoning, knowledge, tools, workflows, human decisions, governance, and distributed execution as executable software.

> **The prompt is source code. The model is not the runtime.**

PPL source is parsed into an AST, compiled into a portable Prompt Intermediate Representation (PIR), lowered into an execution graph, and run by a provider-neutral runtime with durable local state.

## Current version: 0.9

PPL 0.9 makes the graph runtime real on a single machine:

- durable file-backed execution store
- graph-driven interpretation of workflows
- file knowledge sources and JSON memory
- fail-closed tools (`create_ticket`, `echo`, `write_json`)
- human approval pause / `ppl approve` / resume
- WAIT predicates (duration, context path, file)
- overlapping PARALLEL branches
- local multiprocessing workers (`--workers N`)

Still stubbed / out of scope: remote workers, Anthropic/Google adapters, IDE.

Previous releases added:

- 0.2 — model abstraction and typed cognitive output
- 0.3 — knowledge, memory, tools, human decisions
- 0.4 — governance, authorization, budgets, evaluation, provenance
- 0.5 — developer experience and onboarding
- 0.6 — real AI provider adapters
- 0.7 — production-runtime foundations
- 0.8 — execution-graph specification and primitives

## New developer? Start here

1. Read [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).
2. Run [`examples/hello_world.ppl`](examples/hello_world.ppl).
3. Study [`examples/incident.ppl`](examples/incident.ppl).
4. Study [`examples/governed_change.ppl`](examples/governed_change.ppl).
5. Study [`examples/enterprise_automation.ppl`](examples/enterprise_automation.ppl).
6. Read [`docs/TUTORIAL.md`](docs/TUTORIAL.md).
7. Read [`docs/SPEC.md`](docs/SPEC.md).
8. Study [`docs/PPL_0.9.md`](docs/PPL_0.9.md).

## Quick start

```bash
python -m pip install -e .
ppl check examples/hello_world.ppl
ppl compile examples/hello_world.ppl
ppl run examples/hello_world.ppl
ppl run examples/incident.ppl
ppl trace examples/incident.ppl
ppl run examples/governed_change.ppl
ppl run examples/enterprise_automation.ppl
ppl run examples/hello_world.ppl --workers 2
ppl fmt examples/hello_world.ppl
ppl test
```

Pause / resume:

```bash
ppl run app.ppl --execution-id demo
ppl approve demo APPROVE --resume --file app.ppl
ppl resume demo --file app.ppl
```

The bundled local cognitive adapter remains deterministic for offline development. Real model execution is available through the provider-neutral AI runtime adapters (`PPL_AI_PROVIDER=openai`).

## Architecture

```text
PPL Source
    |
    v
Parser -> AST -> Semantic Checks -> PIR
                                      |
                                      v
                             Execution Graph
                                      |
                          FileExecutionStore
                                      |
          +---------------------------+--------------------------+
          |                           |                          |
    Deterministic                 Cognitive                    Human
          |                           |                          |
       Rules/IF                 AI Gateway/Models          Pause/Resume
          |                           |                          |
          +---------------------------+--------------------------+
                                      |
                       Knowledge / Memory / Tools
                                      |
                         Local process workers (optional)
```

## Repository map

- `docs/GETTING_STARTED.md` — beginner onboarding
- `docs/TUTORIAL.md` — step-by-step tutorial
- `docs/EXAMPLES.md` — examples and learning path
- `docs/SPEC.md` — canonical language specification
- `docs/PPL_0.9.md` — durable runtime and local workers
- `docs/REAL_AI_RUNTIME.md` — real model setup
- `examples/` — language and runtime examples
- `src/ppl/` — reference implementation
- `tests/` — executable tests

## Status

PPL is experimental. The 0.x releases explore language semantics and runtime architecture. Syntax and runtime contracts may change before 1.0.
