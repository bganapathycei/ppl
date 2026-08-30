# PPL 0.9 — Real Runtime and Local Workers

> Current release is **0.10**. This note covers the durable graph runtime. Onboarding: [GETTING_STARTED.md](GETTING_STARTED.md). Providers: [PPL_0.10.md](PPL_0.10.md).

PPL 0.9 turns the 0.8 graph keywords into a durable, pausable local runtime and adds a single-machine worker process pool.

## Goals

- durable execution state on disk
- graph-driven interpretation of compiled PIR
- file-backed knowledge and JSON memory
- fail-closed tools
- human approval pause/resume
- WAIT predicates
- true overlapping PARALLEL branches
- local multiprocessing workers (not a distributed cluster)

## Durable store

Executions are persisted under `.ppl/executions/<execution_id>.json`.

```bash
export PPL_STATE_DIR=/path/to/executions   # optional override
ppl run app.ppl --execution-id demo-1
ppl resume demo-1 --file app.ppl
```

Each record includes node statuses, context, checkpoints, wait payload, events, and result.

## Knowledge, memory, tools

- `SOURCE name` loads `knowledge/name.md` (or `.txt` / `.json`) relative to the program, `examples/knowledge`, or `PPL_KNOWLEDGE_DIR`.
- `MEMORY` persists to `.ppl/memory/<App>.json` (or `PPL_MEMORY_DIR`).
- `CALL Tool.action` resolves builtins (`echo`, `write_json`, `create_ticket`) or mappings in `ppl.tools.json`. Unknown actions fail closed.

## Human approval and WAIT

```bash
ppl run app.ppl          # may exit with status WAITING
ppl approve <id> APPROVE --resume --file app.ppl
```

`PPL_HUMAN_DECISION` still auto-resolves for CI.

WAIT predicates:

- duration: `WAIT 1s` / `WAIT 500ms`
- context path: `WAIT order.paid`
- file: `WAIT file:.ppl/events/paid`

## Parallelism and workers

Independent PARALLEL branches run concurrently (sync handlers execute in threads).

```bash
ppl run app.ppl --workers 2
ppl worker --file app.ppl --store .ppl/executions
```

Workers share `FileExecutionStore` and claim PENDING ready nodes. This is a **local process pool**, not remote orchestration.

## Still out of scope (for 0.9)

Anthropic and Google adapters shipped in [PPL 0.10](PPL_0.10.md). Remaining non-goals of the 0.9 slice:

- IDE / language server
- Kubernetes, message queues, or network RPC
- Exactly-once side effects
- Cross-provider fallback chains

## Example

See `examples/enterprise_automation.ppl` and `examples/knowledge/`.
