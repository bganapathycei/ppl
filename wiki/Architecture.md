# Architecture

## End-to-end pipeline

```text
PPL Source (.ppl)
    |
    v
Parser  →  AST
    |
    v
Semantic validation
    |
    v
Compiler  →  PIR (version 0.9+)
    |
    v
Execution graph (DAG)
    |
    v
FileExecutionStore  (.ppl/executions/)
    |
    +-- Deterministic nodes  (RECEIVE, RUN, IF, RETURN, CALL, PARALLEL, JOIN, WAIT)
    +-- Cognitive nodes      (CLASSIFY, EXTRACT, REASON via AI Gateway)
    +-- Human nodes          (HUMAN_APPROVAL → WAITING → resume)
    |
    v
Knowledge / Memory / Tools
    |
    v
Optional local workers (--workers N)
```

## Execution classes

| Class | Letter | Examples |
|---|---|---|
| Deterministic | D | `IF`, `RETURN`, `CALL`, `PARALLEL`, `JOIN`, `WAIT` |
| Cognitive | C | `CLASSIFY`, `EXTRACT`, `REASON` |
| Human | H | `HUMAN_APPROVAL` |

## Key components

| Module | Role |
|---|---|
| `parser.py` | `.ppl` → AST |
| `compiler.py` | AST → PIR + execution graph |
| `runtime.py` | Graph interpreter, cognitive dispatch, human pause |
| `execution_graph.py` | Node/execution state machine |
| `store.py` | `FileExecutionStore` — durable JSON executions |
| `ai_gateway.py` | `AIRequest` / `AIResponse`, `LocalModelAdapter` |
| `provider.py` | Provider registry (`PPL_AI_PROVIDER`) |
| `providers/` | HTTP adapters (OpenAI-compat, Anthropic, Google) |
| `knowledge.py` | File-backed knowledge + JSON memory |
| `tools.py` | Builtin tools + `ppl.tools.json` overrides |
| `workers.py` | Local multiprocessing worker pool |
| `cli.py` | `ppl` command-line interface |

## Cognitive path

```text
CLASSIFY / EXTRACT / REASON
        |
        v
   AIRequest (operation, schema, policy, input)
        |
        v
  CognitiveRuntime (retry, same-adapter fallback)
        |
        v
     AIGateway
        |
        v
  Provider registry → HTTP adapter
        |
        v
   AIResponse
        |
        v
  Schema validation → program context
```

## Durable execution

Each run can persist under `.ppl/executions/<execution_id>.json`:

- node statuses and outputs
- application context
- checkpoints
- wait payload (human / WAIT predicate)
- final result

Override store location: `PPL_STATE_DIR` or `--store`.

## Provider neutrality

`.ppl` source declares **intent** (`MODEL_POLICY` slots like `reasoning-default`). The runtime substitutes `PPL_AI_MODEL` or provider defaults. No vendor URLs or API keys in source files.

## Visual editor

The browser editor (`editor/serve.py`) mirrors the compile → graph → run pipeline for interactive development:

```text
Canvas document model  →  codegen.js  →  .ppl source
                              ↓
                    POST /api/compile  →  execution graph (inspector)
                              ↓
                    POST /api/run      →  Runtime + FileExecutionStore
                              ↓
                    AI Assistant       →  POST /api/assistant/chat
                                         (live provider, apply valid PPL)
```

The assistant reuses the same HTTP provider adapters as cognitive runtime operations, but is a separate chat path for editing source — not graph execution.

---

**See also:** [[Visual Editor]] · [[Runtime and Execution Graph]] · [[Providers and LLM Configuration]]
