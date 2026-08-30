# PPL — Prompt Programming Language

PPL is an experimental AI-native programming language for expressing deterministic computation, AI reasoning, knowledge, tools, workflows, human decisions, and governance as executable software.

> **The prompt is source code. The model is not the runtime.**

PPL source is parsed into an AST, compiled into a portable Prompt Intermediate Representation (PIR), and executed by a runtime that separates deterministic, cognitive, and human operations.

## Current version: 0.4 draft

PPL 0.4 extends the 0.1–0.3 foundation with the language concepts for governed execution and evaluation:

- `GUARD` for runtime-enforced safety constraints
- `AUTHORIZATION` for required capabilities
- `ENVIRONMENT` for execution context
- `BUDGET` for cost, latency, and step limits
- `TEST` and `EVALUATION` for AI quality validation
- structured execution provenance and diagnostics
- `KNOWLEDGE`, `MEMORY`, `TOOL`, and `HUMAN_APPROVAL` from 0.3

## New developer? Start here

1. Read [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).
2. Run [`examples/hello_world.ppl`](examples/hello_world.ppl).
3. Study [`examples/incident.ppl`](examples/incident.ppl) for multi-agent execution.
4. Study [`examples/governed_change.ppl`](examples/governed_change.ppl) for 0.4 governance.
5. Read [`docs/EXAMPLES.md`](docs/EXAMPLES.md) for the learning path.
6. Read [`docs/SPEC.md`](docs/SPEC.md) for language semantics.

## Quick start

```bash
python -m pip install -e .
ppl check examples/hello_world.ppl
ppl compile examples/hello_world.ppl
ppl run examples/incident.ppl
ppl trace examples/incident.ppl
```

The bundled cognitive engine is a deterministic local stub. It is intentionally provider-neutral so language development does not depend on one model vendor.

## Architecture

```text
PPL Source
    |
    v
Lexer -> Parser -> AST -> Semantic Checks -> PIR
                                      |
                                      v
                               PPL Runtime
                                      |
                 +--------------------+--------------------+
                 |                    |                    |
            Deterministic         Cognitive             Human
                 |                    |                    |
              Rules/IF         AI Gateway/Models     Approval/Review
                 |                    |                    |
                 +--------------------+--------------------+
                                      |
                          Knowledge / Memory / Tools
                                      |
                                  Enterprise
```

## Language layers

```text
0.1  Core language + runtime
0.2  Model abstraction + typed cognitive output
0.3  Knowledge + memory + tools + human decisions
0.4  Governance + evaluation + provenance + budgets
1.0  Production compiler/runtime + deployment
```

## Core design principles

1. **Intent over provider API.** Application source should not be tied to an AI vendor.
2. **Deterministic shell around cognitive operations.** Control flow remains inspectable.
3. **Typed cognitive output.** AI responses become validated program data.
4. **Governance is executable.** Guards and authorization are runtime controls, not suggestions to a model.
5. **Evaluation is programming.** AI behavior must be tested against representative data.
6. **Everything important is observable.** Model, policy, provenance, cost, latency, validation, tools, and human decisions should be traceable.

## Repository map

- `docs/GETTING_STARTED.md` — beginner onboarding
- `docs/EXAMPLES.md` — examples and learning path
- `docs/SPEC.md` — language specification
- `examples/` — runnable language examples
- `src/ppl/` — reference implementation
- `tests/` — executable tests

## Status

PPL is experimental. The 0.x releases are intended to explore language semantics and runtime architecture. Syntax and runtime contracts may change before 1.0.
