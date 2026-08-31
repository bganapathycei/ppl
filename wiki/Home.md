# PPL — Prompt Programming Language

**Current version:** 0.10.0  
**Repository:** [github.com/bganapathycei/ppl](https://github.com/bganapathycei/ppl)

PPL is an experimental **AI-native programming language**. You write `.ppl` source; the runtime compiles it to PIR, lowers it to an execution graph, and runs it with durable local state.

> **The prompt is source code. The model is not the runtime.**

PPL combines deterministic control flow with cognitive operations (classification, extraction, reasoning), enterprise knowledge, memory, tools, human decisions, governance, and graph orchestration — **without embedding vendor API calls in application source**.

---

## Quick start

```bash
git clone https://github.com/bganapathycei/ppl.git
cd ppl
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .
ppl check examples/hello_world.ppl
ppl run examples/hello_world.ppl
```

**Expected:** `"GREETING"` (no API key — default `local` adapter).

---

## Wiki navigation

| Page | Description |
|---|---|
| [[Getting Started]] | Install, first run, daily workflow |
| [[Architecture]] | Compiler, PIR, execution graph, runtime |
| [[Language Reference]] | Syntax, keywords, execution classes |
| [[CLI Reference]] | All `ppl` commands and flags |
| [[Examples]] | Bundled programs with command → input → output |
| [[Runtime and Execution Graph]] | Durable state, PARALLEL, WAIT, workers |
| [[Providers and LLM Configuration]] | OpenAI, Anthropic, Google, OpenRouter, etc. |
| [[Knowledge Memory and Tools]] | KNOWLEDGE, MEMORY, CALL, builtins |
| [[Governance and Human Approval]] | GUARD, BUDGET, HUMAN_APPROVAL, pause/resume |
| [[Repository Structure]] | Source layout and key modules |
| [[Release History]] | 0.2 through 0.10 milestones |

---

## What PPL 0.10 includes

- **Multi-provider LLM registry** — OpenAI-compatible, Anthropic, Google Gemini, OpenRouter, Groq, Ollama
- **Durable graph runtime** — file-backed executions, pause/resume, checkpoints
- **Knowledge & memory** — file sources, JSON persistence
- **Fail-closed tools** — `create_ticket`, `echo`, `write_json`
- **Human-in-the-loop** — `HUMAN_APPROVAL`, `ppl approve`, `ppl resume`
- **Local workers** — `--workers N` process pool (single machine)
- **Developer CLI** — `check`, `compile`, `run`, `trace`, `init`, `fmt`, `test`, `repl`

## What is out of scope (0.10)

- Remote distributed worker cluster
- IDE / language server
- Cross-provider fallback chains
- Vendor SDKs in the runtime (HTTP only)

---

## Design principles

1. **Intent over provider API** — `.ppl` files never name a vendor.
2. **Deterministic shell around cognitive ops** — `IF`, `RETURN`, `CALL` are not prompts.
3. **Typed cognitive outputs** — schema-validated before entering program state.
4. **First-class knowledge, memory, tools, humans** — not bolted-on integrations.
5. **Runtime-enforced governance** — guards and budgets are not prompt instructions.
6. **Observable execution** — traces expose graph nodes, models, latency, tokens.

---

## Status

PPL is **experimental**. Syntax and runtime contracts may change before 1.0.

For the latest docs in the repo: [`docs/`](https://github.com/bganapathycei/ppl/tree/main/docs)
