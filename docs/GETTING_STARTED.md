# Getting started with PPL

This is the new-developer walkthrough. Follow the steps in order. Each step says **what to do**, **what you should see**, and **what it means**.

PPL (Prompt Programming Language) is an experimental AI-native language. You write `.ppl` source. The runtime compiles it, builds an execution graph, and runs that graph. A language model is a worker *behind* the graph — it is not the program.

> **The prompt is source code. The model is not the runtime.**

Current release: **0.10.0**. Python **3.10+**.

| If you want to… | Do this |
|---|---|
| Run your first program today | Steps 1–6 (~15 minutes) |
| Write your own `.ppl` file | Continue through Step 9 |
| Learn the language by example | Step 11, then [TUTORIAL.md](TUTORIAL.md) |
| Contribute to the Python runtime | Step 15 |

---

## What you will have when you finish

- A local install you can run from the terminal
- A first successful `ppl check` and `ppl run`
- A mental model of APP / INPUT / AGENT / WORKFLOW
- A project of your own from `ppl init`
- The recommended loop: check → compile → run → trace
- Pointers for live models, pause/resume, and tests

You do **not** need an API key for Steps 1–14. The default `local` adapter is deterministic and offline.

---

## Mental model (read once)

```text
.ppl source
    -> parser / AST
    -> PIR (Prompt Intermediate Representation)
    -> execution graph
    -> FileExecutionStore  (.ppl/executions/)
         |
         +-- deterministic  (IF, RETURN, CALL, PARALLEL, WAIT)
         +-- cognitive      (CLASSIFY, EXTRACT, REASON) via PPL_AI_PROVIDER
         +-- human          (HUMAN_APPROVAL pause / ppl approve / resume)
```

`.ppl` files never name a vendor. The runtime picks a model adapter from `PPL_AI_PROVIDER` or `ppl.providers.json`.

Every operation is one of:

- **D — Deterministic:** `IF`, `RETURN`, `CALL`, `PARALLEL`, `JOIN`, `WAIT`
- **C — Cognitive:** `CLASSIFY`, `EXTRACT`, `REASON`
- **H — Human:** `HUMAN_APPROVAL`

---

## Step 1 — Prerequisites

Install these before cloning:

1. **Git**
2. **Python 3.10 or newer** (3.11–3.13 are fine)

Check from a terminal:

```bash
python --version
git --version
```

**Windows (PowerShell):** if `python` is not found, try `py --version`. Use `py -3.13` (or your installed version) anywhere this guide says `python`.

**macOS / Linux:** if `python` is not found, use `python3`.

**Tip:** Stay in the repository root (`ppl/`) for every command in this guide unless a step says otherwise. Relative paths such as `examples/hello_world.ppl` only work from there.

---

## Step 2 — Get the source

```bash
git clone https://github.com/bganapathycei/ppl.git
cd ppl
```

If you already have the repo, `cd` into it and skip the clone.

You should see at least:

```text
docs/
examples/
src/ppl/
tests/
pyproject.toml
README.md
```

---

## Step 3 — Create a virtual environment

Use a venv so PPL and its CLI stay isolated from other Python projects.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks the activate script (`cannot be loaded because running scripts is disabled`):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Or skip activation and call the venv Python directly: `.\.venv\Scripts\python.exe` (see Step 4).

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Your prompt should show `(.venv)` when the environment is active.

---

## Step 4 — Install PPL

From the repository root, with the venv active:

```bash
python -m pip install -e .
```

`-e` is an editable install: changes under `src/ppl/` are picked up without reinstalling.

Confirm the CLI is on your PATH:

```bash
ppl -h
```

You should see subcommands including `check`, `compile`, `run`, `trace`, `init`, `fmt`, `test`.

**If `ppl` is not found** after a successful install:

```bash
python -m ppl -h
```

That uses the same CLI. On Windows without activating the venv:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\ppl.exe -h
```

**Tip:** The package name on PyPI-style metadata is `ppl-lang`. The import and CLI are still `ppl`.

---

## Step 5 — Verify the compiler

```bash
ppl check examples/hello_world.ppl
```

You should see:

```text
PPL Compiler 0.10.0
Application: HelloAI
Parsing              OK
Types                OK
Agents               OK
Workflows            OK
Graph                OK
Program is valid.
```

If you see `ERROR: ...` instead, the file path is wrong or you are not in the repo root. `check` only compiles; it does not call a model.

---

## Step 6 — Run your first program

```bash
ppl run examples/hello_world.ppl
```

Expected result (JSON):

```json
"GREETING"
```

No API key is required. The CLI supplies sample input when you omit `--input`. For a program whose first input is named `request`, that sample is:

```json
{"request": {"text": "hello there", "done": true}}
```

**What just happened**

1. The parser built an AST from `hello_world.ppl`.
2. The compiler produced PIR and an execution graph (`RECEIVE` → `RUN Classifier` → `RETURN`).
3. The runtime executed the graph.
4. `CLASSIFY` ran on the local adapter and produced a category.
5. The workflow returned `Classifier.category`, which printed as `"GREETING"`.

**Tip:** With the default `local` adapter, `hello_world.ppl` always returns `"GREETING"`. That adapter is keyword-based for incident-style categories (`DATABASE`, `NETWORK`, …). For `GREETING` / `QUESTION` / `OTHER` it falls through to the first declared category. A live provider (Step 14) will actually classify the text.

---

## Step 7 — Read the source line by line

Open `examples/hello_world.ppl`:

```text
APP HelloAI

INPUT request
    text: TEXT

AGENT Classifier

    INPUT request

    CLASSIFY request.text AS
        GREETING
        QUESTION
        OTHER

    OUTPUT
        category
        confidence

WORKFLOW Main

    RECEIVE request
    RUN Classifier
    RETURN Classifier.category
```

| Block | Role |
|---|---|
| `APP` | Names the program. |
| `INPUT` | Declares structured data the workflow receives. |
| `AGENT` | A cognitive worker. Here it only classifies text. |
| `CLASSIFY … AS` | Constrains the model to the listed categories. |
| `OUTPUT` | Fields the agent puts into context (`Classifier.category`, `Classifier.confidence`). |
| `WORKFLOW` | Deterministic orchestration. It does not call a vendor API. |
| `RECEIVE` | Binds the CLI/runtime input to `request`. |
| `RUN` | Executes the named agent. |
| `RETURN` | Ends the workflow with a value. `Classifier.category` is a field path, not a string literal. |

---

## Step 8 — Inspect compilation and the execution graph

Print PIR (JSON). This is large; skim `application`, `agents`, `workflows`, and `graph`:

```bash
ppl compile examples/hello_world.ppl
```

Run again and print the graph plus a step trace:

```bash
ppl trace examples/hello_world.ppl
```

You should see something like:

```text
Application: HelloAI

Execution: <uuid>
Status: SUCCEEDED

Execution graph
  01_receive             RECEIVE          status=SUCCEEDED  ...
  02_run                 RUN              status=SUCCEEDED  ...
  03_return              RETURN           status=SUCCEEDED  ...

Execution trace
RECEIVE request          [D] ok
RUN Classifier           [D] ok
CLASSIFY                 [C] model=reasoning-default ...
RETURN                   [D] GREETING

Result:
"GREETING"
```

`[D]` is deterministic, `[C]` is cognitive, `[H]` is human. After a run, durable state is under `.ppl/executions/` (gitignored).

**Tip:** Use `trace` whenever a result looks wrong. It shows which node ran and whether the cognitive step actually executed.

---

## Step 9 — Pass your own input

Create a JSON file whose top-level keys match the program `INPUT` names.

**Windows (PowerShell):**

```powershell
@'
{"request": {"text": "What is PPL?"}}
'@ | Set-Content -Encoding utf8 my-input.json

ppl run examples/hello_world.ppl --input my-input.json
```

**macOS / Linux:**

```bash
printf '%s\n' '{"request": {"text": "What is PPL?"}}' > my-input.json
ppl run examples/hello_world.ppl --input my-input.json
```

The `--input` file must be JSON, not PPL. Field names must match the `INPUT` block (`request.text`, not `message` or `prompt`).

---

## Step 10 — Scaffold your own project

```bash
ppl init my-app
ppl check my-app/app.ppl
ppl run my-app/app.ppl
```

Expected:

```text
Created PPL project at my-app
```

then the same check/run behavior as hello world. `ppl init` writes:

```text
my-app/
  app.ppl
  README.md
  examples/
  tests/
```

`app.ppl` is a copy of the hello-world pattern (`APP MyPPLApp`). Edit that file, then `ppl check` / `ppl run` again.

If the directory already has files:

```bash
ppl init my-app --force
```

That overwrites `app.ppl` and `README.md`. Do not use `--force` on a directory you care about until you have a backup.

### Minimal program you can type yourself

```text
APP MyFirstApp

INPUT request
    text: TEXT

AGENT Classifier
    INPUT request
    CLASSIFY request.text AS
        GREETING
        QUESTION
        OTHER
    OUTPUT
        category
        confidence

WORKFLOW Main
    RECEIVE request
    RUN Classifier
    RETURN Classifier.category
```

Save as `my-app/app.ppl` (or any path), then:

```bash
ppl check my-app/app.ppl
ppl run my-app/app.ppl
```

### Formatting

```bash
ppl fmt my-app/app.ppl        # print formatted source
ppl fmt my-app/app.ppl -w     # write in place
```

The formatter currently trims trailing whitespace and a trailing newline. Use it for consistency, not as a full pretty-printer.

### Interactive compile buffer

```bash
ppl repl
```

Type PPL source, then `:run` to compile the buffer (it does not execute). `:clear` resets, `:quit` exits.

---

## Step 11 — Recommended daily loop

1. Write intent in a `.ppl` file (data, agents, workflow).
2. `ppl check FILE` — fail fast on parse/type/graph errors.
3. `ppl compile FILE` — inspect PIR when check is not enough.
4. `ppl run FILE` and `ppl trace FILE` against sample JSON.
5. Add `GUARD` / `HUMAN_APPROVAL` before any write-capable `CALL`.
6. Connect a live provider only after local traces look right.

Start with **recommendations**, not autonomous production actions.

---

## Step 12 — Run the bundled examples (in this order)

All of these work offline with the local adapter. Stay in the repo root. Full transcripts (command → input → output → graph): [EXAMPLES.md](EXAMPLES.md).

| Order | Command | Local output | What you are learning |
|---|---|---|---|
| 1 | `ppl run examples/hello_world.ppl` | `"GREETING"` | APP, INPUT, CLASSIFY, WORKFLOW |
| 2 | `ppl run examples/incident.ppl` | `"AUTOMATE"` | Two agents, `MODEL_POLICY`, `IF` on a score |
| 3 | `ppl run examples/governed_change.ppl` | `"APPROVED"` | `GUARD`, `AUTHORIZATION`, `BUDGET` |
| 4 | `ppl run examples/enterprise_automation.ppl` | `"DATABASE"` | Knowledge, memory, `CALL create_ticket` |

### Incident — default vs custom input

```bash
ppl run examples/incident.ppl
# -> "AUTOMATE"
# CLI input: repeated database connection pool failure

ppl run examples/incident.ppl --input examples/incident.json
# -> "AUTOMATE"
```

To see another branch, use a one-off description (no “repeated” / database keywords):

```bash
ppl run examples/incident.ppl --input keep-human.json
# -> "KEEP_HUMAN"   (local automation score ~42)
```

### Governed change

```bash
ppl run examples/governed_change.ppl
# -> "APPROVED"
```

Local `confidence` is **0.92**, so `HUMAN_APPROVAL` is skipped. Guards/budgets are runtime controls, not prompt text.

### Enterprise automation

```bash
ppl run examples/enterprise_automation.ppl
# -> "DATABASE"
# also appends a line to .ppl/tickets.jsonl
```

Default sample input matches the incident (repeated DB pool). Local confidence is high enough that the human gate is **SKIPPED**. To practice pause/approve, use Step 13.

Work through the same files as lessons in [TUTORIAL.md](TUTORIAL.md).

---

## Step 13 — Pause, approve, and resume

Human approval and `WAIT` persist under `.ppl/executions/` (override with `PPL_STATE_DIR` or `--store`).

The **default** enterprise sample does **not** pause (local confidence ≥ 0.85). Use a low-signal payload to exercise the gate. Save as `needs-approval.json`:

```json
{
  "incident": {
    "description": "Odd intermittent glitch",
    "application": "Portal",
    "priority": "P3",
    "id": "INC-77"
  }
}
```

Give the run a stable id:

```bash
ppl run examples/enterprise_automation.ppl --input needs-approval.json --execution-id demo
```

If the process is a TTY, you get an interactive prompt:

```text
HUMAN_APPROVAL [demo]
Question: validate the analysis before continuing
Options: APPROVE, REJECT
Decision>
```

Type `APPROVE` or `REJECT`.

If there is no TTY (CI, some IDE terminals), the run **pauses** and the CLI exits with status **2**. Status 2 means `WAITING`, not a crash.

Then record a decision and continue:

```bash
ppl approve demo APPROVE --resume --file examples/enterprise_automation.ppl
```

Or approve and resume as two commands:

```bash
ppl approve demo APPROVE --file examples/enterprise_automation.ppl
ppl resume demo --file examples/enterprise_automation.ppl
```

For CI / scripts, skip the prompt:

**bash**

```bash
export PPL_HUMAN_DECISION=APPROVE
ppl run examples/enterprise_automation.ppl --input needs-approval.json
```

**PowerShell**

```powershell
$env:PPL_HUMAN_DECISION = "APPROVE"
ppl run examples/enterprise_automation.ppl --input needs-approval.json
```

A successful enterprise run returns a category (often `"ACCESS"` or `"DATABASE"`) and appends a ticket line to `.ppl/tickets.jsonl`.

**Tip:** Always pass `--file` on `resume` / `approve --resume` if the stored execution has no program path, or if you moved the `.ppl` file.

Optional local workers (same machine, shared file store — not a cluster):

```bash
ppl run examples/hello_world.ppl --workers 2
```

Details: [PPL_0.9.md](PPL_0.9.md). Full I/O catalog: [EXAMPLES.md](EXAMPLES.md).

---

## Step 14 — Knowledge, memory, and tools

`examples/enterprise_automation.ppl` declares:

```text
KNOWLEDGE ITOperations
    SOURCE runbooks
    SOURCE application_catalog
    SOURCE historical_incidents

MEMORY IncidentHistory
    KEY incident.id

TOOL ServiceManagement
    ACTION create_ticket
    INPUT
        title: TEXT
        description: TEXT
        priority: TEXT
```

How the runtime resolves those names:

| Declaration | Where it lives |
|---|---|
| `SOURCE name` | `knowledge/name.md` (or `.txt` / `.json`) next to the program, under `examples/knowledge`, or `PPL_KNOWLEDGE_DIR` |
| `MEMORY` | `.ppl/memory/<AppName>.json` (or `PPL_MEMORY_DIR`) |
| `CALL Tool.action` | Builtins `echo`, `write_json`, `create_ticket`, or mappings in `ppl.tools.json`. Unknown actions **fail closed**. |

Sample knowledge files: `examples/knowledge/*.md`.

**Tip:** Put write-capable tools behind `HUMAN_APPROVAL` (or a `GUARD`) until you trust the cognitive path. `create_ticket` in this repo only appends JSON lines locally; a real ITSM mapping would be configured in `ppl.tools.json`.

---

## Step 15 — Optional: a live model

Leave `PPL_AI_PROVIDER` unset (or `local`) while learning. To call a real model, **keep the same `.ppl` file** and configure the runtime only:

**bash**

```bash
export PPL_AI_PROVIDER=openai
export OPENAI_API_KEY=...
export PPL_AI_MODEL=gpt-4.1-mini
ppl run examples/hello_world.ppl
```

**PowerShell**

```powershell
$env:PPL_AI_PROVIDER = "openai"
$env:OPENAI_API_KEY = "..."
$env:PPL_AI_MODEL = "gpt-4.1-mini"
ppl run examples/hello_world.ppl
```

Supported values include `openai`, `openrouter`, `groq`, `ollama`, `anthropic`, `google` / `gemini`, `openai-compatible`, `openai-responses`.

Optional project file `ppl.providers.json` (do not put secrets in git):

```json
{
  "provider": "openai",
  "model": "gpt-4.1-mini"
}
```

Environment variables override the file.

Full setup: [REAL_AI_RUNTIME.md](REAL_AI_RUNTIME.md) and [PPL_0.10.md](PPL_0.10.md).

**Never commit API keys.** Prefer env vars over committing `ppl.providers.json` with `api_key`.

---

## Step 16 — If you are contributing to the runtime

The language lives in `.ppl` files. The reference interpreter is Python under `src/ppl/`.

```text
src/ppl/          parser, compiler, runtime, CLI, providers
examples/         programs you can run
tests/            pytest suite
docs/             this guide and the spec
```

Install pytest in the same venv, then:

```bash
python -m pip install pytest
ppl test
```

Or:

```bash
python -m pytest -q
```

`ppl test` uses pytest when it is installed; otherwise it discovers tests under `tests/` with a small built-in runner.

Useful starting points:

| Task | Where to look |
|---|---|
| CLI flags | `src/ppl/cli.py` |
| Parse / compile | `src/ppl/parser.py`, `src/ppl/compiler.py` |
| Graph execution | `src/ppl/runtime.py`, `src/ppl/execution_graph.py` |
| Local vs live models | `src/ppl/ai_gateway.py`, `src/ppl/provider.py` |
| Language contract | [SPEC.md](SPEC.md) |

After a Python change, re-run `ppl check examples/hello_world.ppl` and `ppl test` before you consider the change done.

---

## CLI reference

| Command | Purpose |
|---|---|
| `ppl check FILE` | Parse, type-check, compile graph |
| `ppl compile FILE` | Print PIR JSON |
| `ppl run FILE` | Execute (`--input`, `--execution-id`, `--workers`, `--store`) |
| `ppl trace FILE` | Execute and print graph + step trace |
| `ppl resume ID --file FILE` | Continue a paused execution |
| `ppl approve ID DECISION --resume --file FILE` | Record a human decision and optionally resume |
| `ppl worker --file FILE` | Claim ready graph nodes from the local store |
| `ppl init DIR` | Scaffold `app.ppl` |
| `ppl fmt FILE` | Format (`-w` writes in place) |
| `ppl test` | Run tests (pytest if installed) |
| `ppl repl` | Interactive compile buffer |

Exit status **2** means the run is `WAITING` (human approval or `WAIT` predicate), not a crash.

---

## Environment variables

| Variable | Role |
|---|---|
| `PPL_AI_PROVIDER` | Adapter: `local` (default), `openai`, `anthropic`, … |
| `PPL_AI_MODEL` | Model id for live providers |
| `PPL_AI_API_KEY` / vendor `*_API_KEY` | Secrets (never commit) |
| `PPL_AI_BASE_URL` | Custom OpenAI-compatible host |
| `PPL_PROVIDERS_FILE` | Path to `ppl.providers.json` |
| `PPL_HUMAN_DECISION` | Auto-answer `HUMAN_APPROVAL` (`APPROVE` / `REJECT`) |
| `PPL_STATE_DIR` | Execution JSON directory (default `.ppl/executions`) |
| `PPL_MEMORY_DIR` | Memory JSON directory |
| `PPL_KNOWLEDGE_DIR` | Extra knowledge root |
| `PPL_TOOLS_FILE` | Path to `ppl.tools.json` |
| `PPL_TICKET_LOG` | Path for builtin `create_ticket` (default `.ppl/tickets.jsonl`) |

---

## Troubleshooting

| Symptom | What to try |
|---|---|
| `python: No module named ppl` | Activate the venv, or `python -m pip install -e .` from the repo root. |
| `ppl` is not recognized | Use `python -m ppl …`, or call `.venv\Scripts\ppl.exe` (Windows) / `.venv/bin/ppl` (Unix). |
| `No such file or directory: examples/hello_world.ppl` | `cd` to the repository root first. |
| `ERROR: ...` from `ppl check` | Read the exception text; most first-day errors are typos in keywords (`WORKFLOW`, `CLASSIFY`) or indentation. |
| Hello world always prints `"GREETING"` | Expected on the local adapter. Set `PPL_AI_PROVIDER` to a live provider to classify real text. |
| `ppl run` exits with status 2 | The graph is `WAITING`. Use `ppl approve` / `ppl resume`, or set `PPL_HUMAN_DECISION`. |
| Enterprise example “hangs” on `Decision>` | Type `APPROVE` or `REJECT`, or run non-interactively with `PPL_HUMAN_DECISION=APPROVE`. |
| Live provider errors about API keys | Unset `PPL_AI_PROVIDER` to go back to `local`, or set the vendor key from [REAL_AI_RUNTIME.md](REAL_AI_RUNTIME.md). |
| Knowledge looks empty | Put `name.md` next to the program, in `examples/knowledge/`, or set `PPL_KNOWLEDGE_DIR`. |
| Tests fail with “pytest not found” | `python -m pip install pytest` then `ppl test`. |

---

## Tips that save time

- **Stay offline until traces look right.** The local adapter is the fastest way to learn syntax and control flow.
- **Name executions** (`--execution-id demo`) as soon as you use approval or workers. UUID ids are harder to resume by hand.
- **Match JSON keys to `INPUT` names.** `incident.ppl` expects `{"incident": {...}}`, not `{"request": {...}}`.
- **`RETURN Classifier.category` reads context.** Returning the string `"Classifier.category"` is a different program.
- **Do not put vendors in `.ppl` files.** Switch models with env vars or `ppl.providers.json`.
- **Treat tools as fail-closed.** If an action is not a builtin and not in `ppl.tools.json`, the run should fail rather than invent a call.
- **`.ppl/` on disk is runtime state**, not source. It is gitignored. Safe to delete if you want a clean slate.

---

## Core building blocks (cheat sheet)

```text
CLASSIFY request.text AS
    GREETING
    QUESTION
    OTHER

EXTRACT
    customer_name
    contract_number

REASON
    determine whether this order presents unusual risk
    OUTPUT:
        risk: TEXT
        confidence: CONFIDENCE
```

Deterministic workflow:

```text
WORKFLOW Main
    RECEIVE request
    RUN Classifier
    IF Classifier.confidence < 0.90
        HUMAN_APPROVAL
    RETURN Classifier.category
```

---

## Where to go next

1. [TUTORIAL.md](TUTORIAL.md) — six short lessons on the bundled examples (do these in order).
2. [EXAMPLES.md](EXAMPLES.md) — example index and first-app ideas.
3. [REAL_AI_RUNTIME.md](REAL_AI_RUNTIME.md) — live providers.
4. [PPL_0.9.md](PPL_0.9.md) — durable graph runtime and local workers.
5. [PPL_0.10.md](PPL_0.10.md) — multi-provider adapters.
6. [SPEC.md](SPEC.md) — language specification (draft 0.10).
