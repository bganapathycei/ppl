# Runtime and Execution Graph

PPL 0.9+ executes compiled workflows as a **durable directed execution graph**.

## Graph nodes

Every workflow step becomes a node with:

- stable `node_id` (e.g. `01_receive`, `02_run`)
- `operation` type
- `dependencies` (DAG edges)
- runtime `status`, `output`, `error`

```text
01_receive (RECEIVE)
    |
    v
02_run (RUN)
    |
    v
03_if (IF) ──► 04_human_approval (HUMAN_APPROVAL)
    |                    |
    +──── 05_join (JOIN) ◄┘
              |
              v
         06_call (CALL)
              |
              v
         07_return (RETURN)
```

## Durable store

Executions persist as JSON:

```text
.ppl/executions/<execution_id>.json
```

Override: `PPL_STATE_DIR` or `ppl run --store PATH`

Each record includes:

- execution and node statuses
- application context
- checkpoints
- wait payload
- events and final result

### Named executions

```bash
ppl run app.ppl --execution-id demo-1
ppl resume demo-1 --file app.ppl
```

## PARALLEL and JOIN

```text
PARALLEL
    RUN RiskAnalyzer
    RUN ComplianceAnalyzer
JOIN RiskAnalyzer
```

Independent branches may overlap. With `--workers N`, branches can run in separate processes sharing the store.

## WAIT predicates

| Form | Meaning |
|---|---|
| `WAIT 1s` / `WAIT 500ms` | Duration |
| `WAIT order.paid` | Context path must be truthy |
| `WAIT file:.ppl/events/paid` | File must exist |

Status becomes `WAITING` until the predicate resolves.

## CHECKPOINT and RESUME

`CHECKPOINT name` persists resumable state. Resumed runs restore completed nodes and must not silently re-run non-idempotent side effects.

## Human approval flow

```text
RUNNING → WAITING → RESUMING → RUNNING
```

```bash
ppl run app.ppl                    # may exit 2 = WAITING
ppl approve <id> APPROVE --resume --file app.ppl
```

CI shortcut: `PPL_HUMAN_DECISION=APPROVE`

## Local workers

```bash
ppl run app.ppl --workers 2
ppl worker --file app.ppl --store .ppl/executions
```

Workers claim `PENDING` ready nodes from `FileExecutionStore`. This is a **single-machine process pool**, not a remote cluster.

## Node failure

Failed nodes set execution status `FAILED` with error metadata. Node-level retry is supported for cognitive operations via `MODEL_POLICY`.

## Observability

`ppl trace` exposes:

- graph version and node statuses
- step trace with `[D]` / `[C]` / `[H]` markers
- model, latency, tokens, cost for cognitive steps
- worker assignment (when using `--workers`)

## Visual editor preview

The browser editor (`python editor/serve.py`) calls `POST /api/compile` to render the same execution graph in the inspector pane, and `POST /api/run` for in-browser execute/trace/human resume. See [[Visual Editor]].

---

**See also:** [[Visual Editor]] · [[Architecture]] · [[Governance and Human Approval]]
