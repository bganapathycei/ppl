# Getting Started

**Requires:** Python 3.10+, Git  
**Current release:** 0.10.0

## 1. Clone and install

```bash
git clone https://github.com/bganapathycei/ppl.git
cd ppl
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

**macOS / Linux:**

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Verify:

```bash
ppl -h
# or: python -m ppl -h
```

## 2. First program

```bash
ppl check examples/hello_world.ppl
ppl run examples/hello_world.ppl
```

| Step | What you see |
|---|---|
| `check` | `PPL Compiler 0.10.0` … `Program is valid.` |
| `run` | `"GREETING"` |

No API key required. The CLI injects sample input when you omit `--input`:

```json
{"request": {"text": "hello there", "done": true}}
```

## 3. Mental model

```text
.ppl source
  → parser / AST
  → PIR (Prompt Intermediate Representation)
  → execution graph
  → FileExecutionStore (.ppl/executions/)
       ├── deterministic  (IF, RETURN, CALL, PARALLEL, WAIT)
       ├── cognitive      (CLASSIFY, EXTRACT, REASON)
       └── human          (HUMAN_APPROVAL)
```

## 4. Run bundled examples

From the repository root:

| Command | Local output |
|---|---|
| `ppl run examples/hello_world.ppl` | `"GREETING"` |
| `ppl run examples/incident.ppl` | `"AUTOMATE"` |
| `ppl run examples/governed_change.ppl` | `"APPROVED"` |
| `ppl run examples/enterprise_automation.ppl` | `"DATABASE"` |

See [[Examples]] for full command → input → output transcripts.

## 5. Scaffold your own project

```bash
ppl init my-app
ppl run my-app/app.ppl
```

## 6. Daily development loop

1. Write `.ppl` source
2. `ppl check FILE`
3. `ppl compile FILE` (inspect PIR)
4. `ppl run FILE` / `ppl trace FILE`
5. Add `GUARD` / `HUMAN_APPROVAL` before write-capable `CALL`s
6. Connect a live provider only after local traces look right — see [[Providers and LLM Configuration]]

## 7. Visual editor (optional)

```bash
python editor/serve.py
```

Open **http://127.0.0.1:8765/** — palette, canvas, inspector (source / run / graph), and **AI Assistant** on the right.

See [[Visual Editor]] for the full workflow, provider setup, and HTTP API.

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `ppl` not found | Use `python -m ppl` or activate venv |
| `ERROR: ...` on check | Run from repo root; verify file path |
| Exit code **2** on run | Execution is `WAITING` (human approval) — use `ppl approve` or `PPL_HUMAN_DECISION=APPROVE` |
| Live provider auth error | Unset `PPL_AI_PROVIDER` to return to `local` |
| AI assistant unavailable | Start `python editor/serve.py`; configure a live provider for chat |

---

**Next:** [[Visual Editor]] · [[Language Reference]] · [[CLI Reference]] · [[Examples]]
