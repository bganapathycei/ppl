# PPL — Prompt Programming Language

PPL is an experimental AI-native programming language for expressing deterministic computation, AI reasoning, knowledge, tools, workflows, human decisions, governance, and distributed execution as executable software.

> **The prompt is source code. The model is not the runtime.**

PPL source is parsed into an AST, compiled into a portable Prompt Intermediate Representation (PIR), lowered into an execution graph, and run by a provider-neutral runtime with durable local state.

## Current version: 0.10

PPL 0.10 adds a multi-provider LLM registry. `.ppl` source stays vendor-free. Live adapters: OpenAI-compatible Chat Completions (OpenAI, OpenRouter, Groq, Ollama), native Anthropic, native Google Gemini, plus optional OpenAI Responses.

PPL 0.9 made the graph runtime real on a single machine:

- durable file-backed execution store
- graph-driven interpretation of workflows
- file knowledge sources and JSON memory
- fail-closed tools (`create_ticket`, `echo`, `write_json`)
- human approval pause / `ppl approve` / resume
- WAIT predicates (duration, context path, file)
- overlapping PARALLEL branches
- local multiprocessing workers (`--workers N`)

Still out of scope: remote distributed workers, IDE, cross-provider fallback chains.

Previous releases added:

- 0.2 — model abstraction and typed cognitive output
- 0.3 — knowledge, memory, tools, human decisions
- 0.4 — governance, authorization, budgets, evaluation, provenance
- 0.5 — developer experience and onboarding
- 0.6 — real AI provider adapters
- 0.7 — production-runtime foundations
- 0.8 — execution-graph specification and primitives
- 0.9 — durable graph runtime and local workers

## New developer? Start here

Follow **[`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)** from Step 1. It is a numbered walkthrough (clone, virtualenv, install, first run, your own project, examples, pause/resume, troubleshooting). You do not need an API key until you choose a live provider.

Condensed path:

1. Clone this repo and `cd` into it.
2. Create a venv, then `python -m pip install -e .`
3. `ppl check examples/hello_world.ppl` then `ppl run examples/hello_world.ppl` — expect `"GREETING"`.
4. Work through Getting Started Steps 7–12, then [`docs/TUTORIAL.md`](docs/TUTORIAL.md).
5. Follow [`docs/EXAMPLES.md`](docs/EXAMPLES.md) for each sample’s **command → input → output** (`incident` → `"AUTOMATE"`, `governed_change` → `"APPROVED"`, `enterprise_automation` → `"DATABASE"`).
6. Read [`docs/SPEC.md`](docs/SPEC.md) only after you have run programs.

Doc index: [`docs/README.md`](docs/README.md).

## Quick start

Requires Python 3.10+. From the repository root (use a virtualenv; see Getting Started Steps 3–4):

```bash
python -m pip install -e .
ppl check examples/hello_world.ppl
ppl run examples/hello_world.ppl
```

If `ppl` is not on your PATH, use `python -m ppl` instead. `ppl check` prints `PPL Compiler 0.10.0`. `ppl run` on hello world returns `"GREETING"` with the default local adapter (no API key). Expected I/O for every bundled example: [`docs/EXAMPLES.md`](docs/EXAMPLES.md).

```bash
ppl compile examples/hello_world.ppl
ppl run examples/incident.ppl                  # "AUTOMATE"
ppl trace examples/incident.ppl
ppl run examples/governed_change.ppl           # "APPROVED"
ppl run examples/enterprise_automation.ppl    # "DATABASE" (+ .ppl/tickets.jsonl)
ppl run examples/hello_world.ppl --workers 2
ppl init my-app
ppl fmt examples/hello_world.ppl
ppl test
```

Full command → input → output for each sample: [`docs/EXAMPLES.md`](docs/EXAMPLES.md). Pause/resume practice uses a low-confidence payload (Getting Started Step 13).

Pause / resume:

```bash
ppl run app.ppl --execution-id demo
ppl approve demo APPROVE --resume --file app.ppl
ppl resume demo --file app.ppl
```

Without installing the package: `python -m ppl check examples/hello_world.ppl`.

The default `local` adapter is deterministic for offline development. Live models: set `PPL_AI_PROVIDER` (`openai`, `openrouter`, `anthropic`, `google`, `groq`, `ollama`, …). See [`docs/REAL_AI_RUNTIME.md`](docs/REAL_AI_RUNTIME.md).

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

- `docs/README.md` — documentation index
- `docs/GETTING_STARTED.md` — numbered new-developer walkthrough (install through first app)
- `docs/TUTORIAL.md` — six lessons on the bundled examples
- `docs/EXAMPLES.md` — examples with command-line inputs and outputs
- `docs/SPEC.md` — canonical language specification (draft 0.10)
- `docs/PPL_0.9.md` — durable runtime and local workers
- `docs/PPL_0.10.md` — multi-provider LLM adapters
- `docs/REAL_AI_RUNTIME.md` — real model setup
- `docs/PPL_0.5.md` … `PPL_0.8.md` — historical release notes
- `examples/` — language and runtime examples
- `src/ppl/` — reference implementation
- `tests/` — executable tests

## Status

PPL is experimental. The 0.x releases explore language semantics and runtime architecture. Syntax and runtime contracts may change before 1.0.
