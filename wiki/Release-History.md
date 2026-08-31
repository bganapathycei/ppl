# Release History

PPL is experimental. Version **0.10.0** is the current release.

## 0.10 — Multi-provider LLM runtime

- Provider registry via `PPL_AI_PROVIDER` and `ppl.providers.json`
- OpenAI-compatible Chat Completions (OpenAI, OpenRouter, Groq, Ollama)
- Native Anthropic Messages adapter
- Native Google Gemini `generateContent` adapter
- Optional OpenAI Responses API adapter
- Structured JSON request + schema re-validation
- `MODEL_POLICY` placeholder → `PPL_AI_MODEL` substitution
- No vendor SDKs (HTTP only)

## 0.9 — Durable graph runtime and local workers

- `FileExecutionStore` — `.ppl/executions/<id>.json`
- Graph-driven interpretation of compiled PIR
- File-backed knowledge (`SOURCE`) and JSON memory
- Fail-closed builtin tools
- `HUMAN_APPROVAL` pause / `ppl approve` / `ppl resume`
- `WAIT` predicates (duration, context path, file)
- Overlapping `PARALLEL` branches
- Local multiprocessing workers (`--workers N`, `ppl worker`)

## 0.8 — Execution graph specification

- Workflows compile to explicit DAGs
- `PARALLEL`, `JOIN`, `WAIT`, `CHECKPOINT` keywords
- Node IDs, dependencies, status model
- Path to distributed workers without source changes

## 0.7 — Production runtime foundations

- Async cognitive contract
- Typed runtime errors and retry/backoff hooks
- Durable execution state abstraction
- Execution IDs and resumable state
- Model-aware pricing abstraction
- Secret separation from source

## 0.6 — Real AI runtime

- `ModelAdapter` interface
- OpenAI HTTP adapter
- Environment-based configuration
- Schema-validated cognitive outputs
- Retry and fallback via `MODEL_POLICY`
- Execution telemetry
- Local offline fallback

## 0.5 — Developer experience

- `ppl init` project scaffolding
- `ppl fmt` formatting
- `ppl test` test runner
- `ppl repl` interactive buffer
- Readable diagnostics

## 0.4 — Governance

- `GUARD`, `AUTHORIZATION`, `BUDGET`
- Confidence-based human approval
- Evaluation and provenance concepts

## 0.3 — Enterprise primitives

- `KNOWLEDGE`, `MEMORY`, `TOOL`
- `HUMAN_APPROVAL`
- `CALL` tool actions

## 0.2 — Model abstraction

- Typed cognitive output
- `MODEL_POLICY`
- Provider-neutral AI request/response contract

## Roadmap (not yet shipped)

- Cross-provider fallback chains (0.10.1)
- Remote distributed worker cluster
- IDE / language server
- GitHub Release binaries (PyInstaller/Nuitka)
- Exactly-once external side effects

---

**See also:** [[Home]] · [[Architecture]]
