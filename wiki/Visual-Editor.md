# Visual Editor

The **PPL visual editor** is a browser workspace for building, running, and maintaining PPL 0.10 programs. All code lives in [`editor/`](https://github.com/bganapathycei/ppl/tree/main/editor) in the repository.

## Start

```bash
python editor/serve.py
```

Open **http://127.0.0.1:8765/**

Requires Python 3.10+ and the PPL package on `PYTHONPATH` (or `pip install -e .` from the repo root).

## Layout

```text
Palette  |  Canvas  |  Inspector (Source / Run / Graph)  |  AI Assistant
```

| Panel | Role |
|---|---|
| Palette | Drag or click-to-place constructs (APP, AGENT, WORKFLOW, GUARD, KNOWLEDGE, …) |
| Canvas | Nested blocks with typed drop zones |
| Source | Live `.ppl` from the document model |
| Run | Input JSON, result, trace, human-approval resume |
| Graph | Compiled execution graph (SVG) |
| AI Assistant | Natural-language create/edit; provider and model picker |

## Block editing

1. Drag from the palette onto highlighted slots (invalid parents are rejected).
2. Or **click** a palette item, then **click** a drop zone.
3. Edit names, types, conditions, and instructions inline.
4. Reorder or delete blocks.
5. **Validate**, **Run**, **Download**, or **Open** a `.ppl` file.

Bundled examples match the CLI samples (`hello_world`, `incident`, `governed_change`, `enterprise_automation`).

## Run in the browser

The Run pane mirrors `ppl run`:

- **Input JSON** is prefilled from compile defaults (same as the CLI).
- **Result** and **Trace** show runtime output.
- On `HUMAN_APPROVAL`, decision buttons resume the execution (same as `ppl approve`).

Execution uses the real PPL runtime via `POST /api/run`. The default **local** adapter works without an API key.

## AI coding assistant

The rightmost panel accepts **natural language** prompts to create, edit, or maintain programs — similar to the GitHub Copilot VS Code sidebar.

### Workflow

1. Pick **Provider** and **Model** (OpenAI, OpenRouter, Anthropic, Google, Groq, Ollama, OpenAI-compatible).
2. Describe the change (“add a classifier agent”, “gate low confidence with HUMAN_APPROVAL”, …).
3. Review the reply. When the assistant returns a full program in a ` ```ppl ` block and it parses, click **Apply to editor**.

### Configuration

Uses the same env vars as [[Providers and LLM Configuration]] — set them **before** starting `serve.py`:

```bash
export PPL_AI_PROVIDER=openai
export OPENAI_API_KEY=...
export PPL_AI_MODEL=gpt-4.1-mini
python editor/serve.py
```

The assistant requires a **live** provider (not the offline `local` adapter). Program **Run** in the inspector still works offline.

Selections persist in browser `localStorage`.

## HTTP API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/compile` | Parse + compile → graph, default input |
| `POST` | `/api/run` | Execute with trace and human resume |
| `GET` | `/api/assistant/config` | Provider/model catalog and key status |
| `POST` | `/api/assistant/chat` | Assistant chat with optional current source |

## Tests

```bash
python -m pytest editor/tests -q
```

## Limitations

- Single-user dev server (not a production deployment).
- No language server or VS Code extension (see [[Release History]] roadmap).
- Opening `index.html` as a file disables server-backed compile, run, graph, and assistant.

---

**See also:** [[Getting Started]] · [[Providers and LLM Configuration]] · [[Runtime and Execution Graph]] · [[Repository Structure]]
