# PPL visual editor

The **PPL visual editor** is a browser-based workspace for building, running, and maintaining complete PPL 0.10 programs. It lives entirely under [`editor/`](../editor/). The language runtime in `src/ppl/` is unchanged.

## Start the editor

From the repository root (package installed or `src/` on `PYTHONPATH`):

```bash
python editor/serve.py
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/).

Optional flags: `--host`, `--port` (default `127.0.0.1:8765`).

You can open `editor/index.html` as a file for offline block editing and source preview. **Compile**, **run**, **execution-graph preview**, and the **AI assistant** require the server.

## Layout

```text
┌──────────┬─────────────────────┬─────────────────┬──────────────────┐
│ Palette  │ Canvas              │ Inspector       │ AI Assistant     │
│ (blocks) │ (nested program)    │ Source / Run /  │ natural language │
│          │                     │ Graph           │ + provider/model │
└──────────┴─────────────────────┴─────────────────┴──────────────────┘
```

| Panel | Purpose |
|---|---|
| **Palette** | Drag or click-to-place PPL constructs (APP, INPUT, AGENT, WORKFLOW, governance, enterprise, …) |
| **Canvas** | Nested typed drop zones, inline edit, reorder, delete |
| **Inspector — Source** | Live `.ppl` generated from the canvas |
| **Inspector — Run** | Input JSON, result, trace, human-approval buttons |
| **Inspector — Graph** | Compiled execution graph (SVG) |
| **AI Assistant** | Describe changes in natural language; pick provider and model; apply valid PPL back to the canvas |

Programs persist in browser `localStorage`. Use **Download** or **Open** for file-based workflows.

## Daily workflow

1. Load an example or start from **New**.
2. Build on the canvas or ask the **AI Assistant** to create or edit the program.
3. **Validate** to parse and compile.
4. Edit **Input JSON** if needed, then **Run**.
5. If the run pauses on `HUMAN_APPROVAL`, use the decision buttons in the Run pane.
6. **Download** `.ppl` when ready for CLI or git.

## AI coding assistant

The assistant panel (far right) works like a Copilot-style sidebar:

1. Choose **Provider** and **Model** from the dropdowns (OpenAI, OpenRouter, Anthropic, Google, Groq, Ollama, OpenAI-compatible).
2. Describe what you want in plain language — create a program, add a guard, refactor an agent, etc.
3. The assistant replies with explanation and, when editing, a full program inside a ` ```ppl ` fence.
4. When the server validates the proposed source, click **Apply to editor** to load it on the canvas.

The assistant uses the **same environment variables** as the PPL runtime. Configure keys before starting the server:

```bash
export PPL_AI_PROVIDER=openai
export OPENAI_API_KEY=...
export PPL_AI_MODEL=gpt-4.1-mini
python editor/serve.py
```

PowerShell:

```powershell
$env:PPL_AI_PROVIDER = "openai"
$env:OPENAI_API_KEY = "..."
$env:PPL_AI_MODEL = "gpt-4.1-mini"
python editor/serve.py
```

See [REAL_AI_RUNTIME.md](REAL_AI_RUNTIME.md) for all providers. The assistant does **not** use the offline `local` adapter — configure a live provider for chat. Program **Run** still works offline with the local runtime adapter when no live provider is set.

Provider and model choices are remembered in `localStorage`.

## HTTP API

The dev server exposes JSON endpoints used by the UI:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/compile` | Parse and compile `.ppl` source → graph, default input |
| `POST` | `/api/run` | Execute via `Runtime` (trace, human resume, `execution_id`) |
| `GET` | `/api/assistant/config` | Providers, models, key availability, defaults |
| `POST` | `/api/assistant/chat` | Chat with optional `current_source` context |

### Compile

```json
POST /api/compile
{ "source": "APP HelloAI\n..." }
```

### Run

```json
POST /api/run
{
  "source": "APP HelloAI\n...",
  "input": { "request": { "text": "hello there" } },
  "trace": true,
  "execution_id": "optional-uuid",
  "human_decision": "APPROVE"
}
```

### Assistant chat

```json
POST /api/assistant/chat
{
  "provider": "openai",
  "model": "gpt-4.1-mini",
  "current_source": "APP HelloAI\n...",
  "messages": [
    { "role": "user", "content": "Add a HUMAN_APPROVAL when confidence < 0.9" }
  ]
}
```

Response includes `reply`, optional `ppl_source`, `ppl_valid`, and `ppl_error`.

## Tests

```bash
python -m pytest editor/tests -q
```

JS round-trip tests (`parse.js` → `codegen.js` → real `ppl.Compiler`) require Node.js on your PATH.

## See also

- [`editor/README.md`](../editor/README.md) — folder layout and implementation notes
- [GETTING_STARTED.md](GETTING_STARTED.md) — CLI-first onboarding
- [REAL_AI_RUNTIME.md](REAL_AI_RUNTIME.md) — provider and API key setup
- [EXAMPLES.md](EXAMPLES.md) — bundled programs also available from the Example menu
