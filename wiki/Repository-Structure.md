# Repository Structure

**Repository:** [github.com/bganapathycei/ppl](https://github.com/bganapathycei/ppl)

## Top-level layout

```text
ppl/
├── README.md              # Project overview and quick start
├── pyproject.toml         # Package metadata (ppl-lang 0.10.0)
├── docs/                  # In-repo documentation
├── editor/                # Visual editor + AI assistant (serve.py)
├── examples/              # Sample .ppl programs and knowledge files
├── src/ppl/               # Reference interpreter implementation
├── tests/                 # pytest suite
└── .ppl/                  # Runtime state (gitignored): executions, memory, tickets
```

## Documentation (`docs/`)

| File | Purpose |
|---|---|
| `GETTING_STARTED.md` | Numbered new-developer walkthrough |
| `TUTORIAL.md` | Six lessons on bundled examples |
| `EXAMPLES.md` | Command → input → output catalog |
| `SPEC.md` | Language specification (draft 0.10) |
| `PPL_0.9.md` | Durable runtime and workers |
| `PPL_0.10.md` | Multi-provider adapters |
| `REAL_AI_RUNTIME.md` | Live model setup |
| `VISUAL_EDITOR.md` | Browser editor and AI assistant |
| `PPL_0.5.md` … `PPL_0.8.md` | Historical release notes |

## Examples (`examples/`)

| File | Description |
|---|---|
| `hello_world.ppl` | Minimal CLASSIFY workflow |
| `incident.ppl` | Two agents, IF branching, MODEL_POLICY |
| `governed_change.ppl` | GUARD, AUTHORIZATION, BUDGET, HUMAN_APPROVAL |
| `enterprise_automation.ppl` | Knowledge, memory, tools, human gate |
| `real_ai_incident.ppl` | Incident pattern for live providers |
| `incident.json` | Sample input payload |
| `knowledge/*.md` | Knowledge source files |

## Editor (`editor/`)

Self-contained browser editor (vanilla HTML/JS + Python dev server). Does not modify `src/ppl/`.

| Path | Role |
|---|---|
| `serve.py` | Static server; `/api/compile`, `/api/run`, `/api/assistant/*` |
| `assistant.py` | AI coding assistant — provider routing, PPL extraction |
| `index.html`, `css/`, `js/` | UI — palette, canvas, inspector, assistant panel |
| `templates/` | Bundled example `.ppl` files |
| `tests/` | pytest (+ optional Node round-trip) |

Run: `python editor/serve.py` → http://127.0.0.1:8765/

See [[Visual Editor]] and `docs/VISUAL_EDITOR.md`.

## Source (`src/ppl/`)

| Module | Role |
|---|---|
| `cli.py` | `ppl` command-line interface |
| `parser.py` | Lexer/parser → AST |
| `ast.py` | AST node definitions |
| `compiler.py` | AST → PIR + execution graph |
| `runtime.py` | Graph executor, cognitive dispatch |
| `execution_graph.py` | Execution/node state machine |
| `store.py` | `FileExecutionStore` durable persistence |
| `ai_gateway.py` | AI request/response, local adapter |
| `ai_runtime.py` | Cognitive runtime with retry |
| `provider.py` | Provider registry |
| `providers/` | HTTP adapters (openai, anthropic, google, …) |
| `knowledge.py` | Knowledge file loading, memory I/O |
| `tools.py` | Builtin tools and registry |
| `workers.py` | Local multiprocessing workers |
| `schema.py` | Output schema validation |
| `dx.py` | `init`, `fmt`, diagnostics |
| `production_runtime.py` | Error types, retry hooks |

## Tests (`tests/`)

| File | Coverage |
|---|---|
| `test_smoke.py` | End-to-end examples, CLI check |
| `test_runtime_09.py` | Store, knowledge, memory, workers, WAIT |
| `test_providers.py` | Mocked HTTP provider adapters |
| `test_execution_graph.py` | Graph compilation |
| `test_production_runtime.py` | Retry/error classification |

Run: `ppl test` or `python -m pytest tests -q`

## Runtime artifacts (`.ppl/`)

| Path | Content |
|---|---|
| `.ppl/executions/<id>.json` | Durable execution state |
| `.ppl/memory/<App>.json` | Persistent memory |
| `.ppl/tickets.jsonl` | `create_ticket` log |

## Package

- **PyPI name:** `ppl-lang`
- **CLI entry:** `ppl = ppl.cli:main`
- **Module entry:** `python -m ppl`
- **Python:** >= 3.10
- **Dependencies:** none (stdlib only)

---

**See also:** [[Architecture]] · [[CLI Reference]]
