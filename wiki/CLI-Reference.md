# CLI Reference

All commands assume `ppl` is on PATH after `python -m pip install -e .`. Alternative: `python -m ppl <command>`.

## Commands

| Command | Description |
|---|---|
| `ppl check FILE` | Parse, type-check, validate graph |
| `ppl compile FILE` | Print PIR as JSON |
| `ppl run FILE` | Execute program |
| `ppl trace FILE` | Execute and print graph + step trace |
| `ppl resume ID` | Continue paused execution |
| `ppl approve ID DECISION` | Record human decision |
| `ppl worker` | Long-running local graph worker |
| `ppl init DIR` | Scaffold new project |
| `ppl fmt FILE` | Format source (`-w` / `--write` to save) |
| `ppl test [PATH]` | Run tests (default: `tests/`) |
| `ppl repl` | Interactive compile buffer |

## `ppl run` / `ppl trace` flags

| Flag | Description |
|---|---|
| `--input FILE` | JSON input (overrides CLI defaults) |
| `--execution-id ID` | Named durable execution |
| `--workers N` | Local process pool (N > 0) |
| `--store PATH` | Override execution store directory |

## `ppl resume`

```bash
ppl resume <execution_id> --file app.ppl [--store PATH]
```

## `ppl approve`

```bash
ppl approve <execution_id> <DECISION> [--file app.ppl] [--store PATH] [--resume]
```

Example:

```bash
ppl approve demo APPROVE --resume --file examples/enterprise_automation.ppl
```

## `ppl worker`

```bash
ppl worker --file app.ppl [--store PATH] [--name worker-1]
```

Claims ready graph nodes from the shared store. Stop with Ctrl+C.

## `ppl init`

```bash
ppl init my-app [--force]
```

Creates `app.ppl`, `examples/`, `tests/`, `README.md`.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Error (parse, runtime, missing file) |
| `2` | Execution `WAITING` (human approval or WAIT) |

## Default CLI inputs

When `--input` is omitted, the CLI supplies sample JSON based on the first `INPUT` block:

| Input name | Sample theme |
|---|---|
| `request` | `{"text": "hello there", "done": true}` |
| `incident` | Repeated database connection pool failure |
| `change` | Production pool increase |

## Environment variables (common)

| Variable | Purpose |
|---|---|
| `PPL_AI_PROVIDER` | Model adapter (`local`, `openai`, `anthropic`, …) |
| `PPL_AI_MODEL` | Default model id |
| `PPL_AI_API_KEY` | Generic API key |
| `PPL_AI_BASE_URL` | OpenAI-compatible base URL |
| `PPL_STATE_DIR` | Execution store root |
| `PPL_KNOWLEDGE_DIR` | Knowledge file search path |
| `PPL_MEMORY_DIR` | Memory JSON directory |
| `PPL_HUMAN_DECISION` | Auto-approve/reject for CI (`APPROVE` / `REJECT`) |
| `PPL_HUMAN_DECISION` | Skip interactive human gate |
| `PPL_PROVIDERS_FILE` | Path to `ppl.providers.json` |
| `PPL_TOOLS_FILE` | Path to `ppl.tools.json` |
| `PPL_TICKET_LOG` | `create_ticket` log path |

Full provider list: [[Providers and LLM Configuration]]

---

**See also:** [[Getting Started]] · [[Examples]]
