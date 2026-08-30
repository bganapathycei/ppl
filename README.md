# PPL — Prompt Programming Language

PPL is an experimental AI-native programming language for expressing deterministic computation, AI reasoning, knowledge, tools, workflows, human decisions, governance, and production runtime behavior as executable software.

> **The prompt is source code. The model is not the runtime.**

PPL source is parsed into an AST, compiled into a portable Prompt Intermediate Representation (PIR), and executed by a runtime that separates deterministic, cognitive, and human operations.

## Current version: 0.7 draft

PPL 0.7 adds the production-runtime foundation:

- asynchronous cognitive execution
- streaming event contracts
- typed provider/runtime error classification
- bounded retry and backoff semantics
- rate-limit-aware execution primitives
- durable execution state abstraction
- resumable execution IDs
- model pricing abstraction
- environment/secret separation

## New developer? Start here

1. Read [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).
2. Run [`examples/hello_world.ppl`](examples/hello_world.ppl).
3. Study [`examples/incident.ppl`](examples/incident.ppl).
4. Study [`examples/governed_change.ppl`](examples/governed_change.ppl).
5. Read [`docs/TUTORIAL.md`](docs/TUTORIAL.md).
6. Read [`docs/PPL_0.7.md`](docs/PPL_0.7.md).
7. Read [`docs/SPEC.md`](docs/SPEC.md).

## Quick start

```bash
python -m pip install -e .
ppl check examples/hello_world.ppl
ppl compile examples/hello_world.ppl
ppl run examples/incident.ppl
ppl trace examples/incident.ppl
```

For real-model execution, configure the provider through environment variables. Never put API keys in `.ppl` source.

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
                  +-------------------+-------------------+
                  |                   |                   |
             Deterministic        Cognitive            Human
                  |                   |                   |
               Rules/IF        AI Gateway/Models     Approval/Review
                  |                   |                   |
                  +-------------------+-------------------+
                                      |
                         Knowledge / Memory / Tools
                                      |
                           Execution State / Trace
                                      |
                                  Enterprise
```

## Language layers

```text
0.1  Core language + runtime
0.2  Model abstraction + typed cognitive output
0.3  Knowledge + memory + tools + human decisions
0.4  Governance + evaluation + provenance + budgets
0.5  Developer experience
0.6  Real AI runtime + provider abstraction
0.7  Production runtime primitives
1.0  Production compiler/runtime + deployment
```

## Core design principles

1. **Intent over provider API.** Application source should not be tied to an AI vendor.
2. **Deterministic shell around cognitive operations.** Control flow remains inspectable.
3. **Typed cognitive output.** AI responses become validated program data.
4. **Governance is executable.** Guards and authorization are runtime controls.
5. **Evaluation is programming.** AI behavior is tested against representative data.
6. **Everything important is observable.** Model, policy, provenance, cost, latency, validation, tools, and human decisions should be traceable.
7. **Production concerns stay in the runtime.** Retry, backoff, streaming, persistence, rate limits, and provider failure mapping do not leak into PPL application syntax.

## Repository map

- `docs/GETTING_STARTED.md` — beginner onboarding
- `docs/TUTORIAL.md` — step-by-step language tutorial
- `docs/EXAMPLES.md` — examples and learning path
- `docs/SPEC.md` — language specification
- `docs/PPL_0.7.md` — production runtime design
- `examples/` — runnable language examples
- `src/ppl/` — reference implementation
- `tests/` — executable tests

## Status

PPL is experimental. The 0.x releases explore language semantics and runtime architecture. Syntax and runtime contracts may change before 1.0.
