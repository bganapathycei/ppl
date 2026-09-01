# PPL Visual Editor

Drag-and-drop editor for complete PPL 0.10 programs. Nested blocks construct `.ppl` source; the inspector shows that source, run output, and a compiled execution-graph preview. An **AI Assistant** panel on the far right edits programs through natural language.

All editor code lives in this folder. The language runtime in `src/ppl/` is unchanged.

Full user guide: [`docs/VISUAL_EDITOR.md`](../docs/VISUAL_EDITOR.md).

## Two canvases

- **Classic editor** (this folder, no build): the toolbar has a **Flow / Blocks** toggle.
  *Flow* is an interactive flowchart (auto-laid-out from the program, with a Properties
  panel); *Blocks* is the original nested-block editor. Open with `python editor/serve.py`.
- **React Flow editor** ([`react/`](react/), optional build): a polished node-canvas front
  end built with `@xyflow/react` + dagre, served at
  [`/flow/`](http://127.0.0.1:8765/flow/) after `npm --prefix editor/react run build`.
  See [`react/README.md`](react/README.md).

Both talk to the same `serve.py` API and reuse the same `.ppl` parser/codegen, so the
generated source is identical across views.

## Run

From the **editor** directory:

**Windows (PowerShell):**

```powershell
.\run.ps1
```

**macOS / Linux:**

```bash
chmod +x run.sh   # first time only
./run.sh
```

Or from anywhere in the repo:

```bash
python editor/serve.py
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/). The run scripts verify Python 3.10+ and open the browser by default (`-NoBrowser` / `--no-browser` to skip).

You can also open `index.html` as a file. Construction, source preview, Open/Download, and examples still work. Compile, run, graph preview, and the AI assistant require the server.

## Layout

```text
editor/
├── index.html          # Shell (palette | canvas | inspector | assistant)
├── css/editor.css
├── serve.py            # Static files + /api/* JSON endpoints
├── run.ps1             # Windows startup script
├── run.sh              # macOS/Linux startup script
├── assistant.py        # AI assistant routing and PPL extraction
├── js/
│   ├── app.js          # Program state, toolbar, run integration
│   ├── assistant.js    # Chat UI, provider/model picker
│   ├── model.js        # Document AST mirror
│   ├── codegen.js      # Document → .ppl
│   ├── parse.js        # .ppl → document (Open, templates, assistant apply)
│   ├── compile.js      # POST /api/compile client
│   ├── run.js          # POST /api/run client
│   └── …               # canvas, palette, graph, validate, …
├── templates/          # Bundled .ppl examples
└── tests/              # pytest + optional Node round-trip
```

## Use

1. Drag constructs from the palette onto highlighted drop zones (typed slots reject invalid parents). You can also click a palette item, then click a drop zone.
2. Edit names, types, conditions, and instructions on the cards.
3. Reorder or delete blocks. Download `.ppl` or copy from the Source pane.
4. Load a bundled example, or Open an existing `.ppl` file.
5. Validate to parse/compile. **Run** to execute with the PPL runtime — edit **Input JSON** first if needed (defaults match the CLI).
6. When a program hits `HUMAN_APPROVAL`, use the decision buttons to resume.
7. Use the **AI Assistant** on the far right — pick provider/model, describe changes in plain language, **Apply to editor** when valid PPL is returned.

## AI assistant

- **UI:** `js/assistant.js` — provider/model dropdowns (Copilot-style), chat, apply button.
- **Backend:** `assistant.py` — system prompt, HTTP calls to the same provider adapters as the runtime, `extract_ppl()` + parser validation before apply.
- **Config:** `GET /api/assistant/config` — catalog and whether API keys are set.
- **Chat:** `POST /api/assistant/chat` — `{ messages, provider, model, current_source }`.

Configure live providers with the same environment variables as the PPL runtime (`PPL_AI_PROVIDER`, `PPL_AI_MODEL`, `PPL_AI_API_KEY`, …). See [`docs/REAL_AI_RUNTIME.md`](../docs/REAL_AI_RUNTIME.md).

## HTTP API

| Method | Path | Body | Response |
|---|---|---|---|
| `POST` | `/api/compile` | `{ "source": "..." }` | `{ ok, graph, default_input, … }` |
| `POST` | `/api/run` | `{ source, input?, trace?, execution_id?, human_decision? }` | `{ ok, result, trace, waiting, … }` |
| `GET` | `/api/assistant/config` | — | `{ ok, providers[], default_provider, default_model }` |
| `POST` | `/api/assistant/chat` | `{ messages[], provider, model, current_source? }` | `{ ok, reply, ppl_source?, ppl_valid, ppl_error? }` |

## Tests

```bash
python -m pytest editor/tests -q
```

JS round-trip tests (`parse.js` → `codegen.js` → real `ppl.Compiler`) require [Node.js](https://nodejs.org/) on your PATH. If Node is missing, those tests are skipped automatically.

Templates under `templates/` are copies of the bundled examples used by the Example menu.
