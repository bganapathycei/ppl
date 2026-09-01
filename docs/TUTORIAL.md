# PPL 0.10 tutorial

Work through these lessons **in order**. Each lesson is a sequence of commands, the output you should see, and a small experiment.

**Before you start:** finish [GETTING_STARTED.md](GETTING_STARTED.md) Steps 1–6 (clone, venv, `pip install -e .`, `ppl check` / `ppl run` on hello world). All commands below assume the venv is active and your current directory is the **repository root**.

You do not need an API key. The default `local` adapter is deterministic.

---

## Lesson 1 — Classify text

**Goal:** Compile and run the smallest useful PPL application, and see that `RETURN` reads agent output.

**File:** `examples/hello_world.ppl`

### 1. Read the program

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

`CLASSIFY` constrains the cognitive result to declared categories. `RETURN Classifier.category` is a field path, not the string `"Classifier.category"`.

### 2. Check, then run

```bash
ppl check examples/hello_world.ppl
ppl run examples/hello_world.ppl
```

**Expected**

- Check ends with `Program is valid.` and `Application: HelloAI`.
- Run prints `"GREETING"`.

The CLI injects `{"request": {"text": "hello there", "done": true}}` when you omit `--input`.

### 3. Try this

Pass your own JSON (keys must match `INPUT request`):

```bash
ppl run examples/hello_world.ppl --input my-input.json
```

**Tip:** On the local adapter this example still prints `"GREETING"` for any text. That adapter’s classifiers are keyword-based for incident categories, not greetings. Use a live provider later if you want the category to follow the sentence.

### What this lesson taught

APP, INPUT, AGENT, CLASSIFY, WORKFLOW, RECEIVE, RUN, RETURN.

---

## Lesson 2 — Two agents and branching

**Goal:** Run a multi-agent workflow and inspect the execution graph.

**File:** `examples/incident.ppl`

`MODEL_POLICY` names model *slots* (`reasoning-default`, …). The runtime substitutes `PPL_AI_MODEL` or the provider default. The workflow is ordinary control flow:

```text
RUN Analyzer
RUN AutomationAdvisor
IF AutomationAdvisor.score >= 80
    RETURN "AUTOMATE"
```

### 1. Run, then trace

```bash
ppl run examples/incident.ppl
```

**Input (CLI default):** repeated database connection pool failure (`INC-1001`).  
**Output:** `"AUTOMATE"`.

```bash
ppl trace examples/incident.ppl
```

The trace lists graph nodes and cognitive steps (`CLASSIFY`, `EXTRACT`, `REASON`) marked `[C]`.

### 2. Try this

Use the sample payload in the repo:

```bash
ppl run examples/incident.ppl --input examples/incident.json
```

Still `"AUTOMATE"` locally: the description includes “database connection pool” and “repeated”.

Save `keep-human.json` with `"description": "One-off laptop screen flicker"` (and any `application` / `priority`), then:

```bash
ppl run examples/incident.ppl --input keep-human.json
```

**Output:** `"KEEP_HUMAN"` (local automation score drops to ~42).

**Tip:** When an `IF` surprises you, `ppl trace` is faster than guessing. Full I/O catalog: [EXAMPLES.md](EXAMPLES.md).

### What this lesson taught

Multiple agents, `MODEL_POLICY`, `IF` / `ELSE IF` / `ELSE`, custom `--input`.

---

## Lesson 3 — Governance and human approval

**Goal:** See runtime governance (not prompt text) and know how pause/resume works.

**File:** `examples/governed_change.ppl`

```text
GUARD ProductionSafety
    NEVER execute production changes
        without authorization

AUTHORIZATION production_change
    REQUIRES production.write

BUDGET
    max_cost: 0.10
    max_steps: 10

IF RiskAnalyzer.confidence < 0.90
    HUMAN_APPROVAL
```

Guards, authorization, and budgets are enforced by the runtime.

### 1. Run the happy path

```bash
ppl run examples/governed_change.ppl
```

**Expected:** `"APPROVED"`. The local adapter returns high confidence (`0.92`) and `safe: true`, so the workflow does **not** pause.

### 2. Practice named executions

```bash
ppl run examples/governed_change.ppl --execution-id change-1
```

If this run ever waits, approve and continue:

```bash
ppl approve change-1 APPROVE --resume --file examples/governed_change.ppl
```

**Tip:** To force a pause in CI you would need a cognitive result with `confidence < 0.90`. The enterprise example in Lesson 4 does that with the local adapter. Exit status **2** means `WAITING`, not a crash. For non-interactive shells, `PPL_HUMAN_DECISION=APPROVE` auto-answers the gate.

### What this lesson taught

`GUARD`, `AUTHORIZATION`, `BUDGET`, confidence-gated `HUMAN_APPROVAL`, `--execution-id`.

---

## Lesson 4 — Knowledge, memory, and tools

**Goal:** Run a program that reads files, may pause for a human, and calls a builtin tool.

**File:** `examples/enterprise_automation.ppl`  
**Knowledge:** `examples/knowledge/*.md`

```text
KNOWLEDGE ITOperations
    SOURCE runbooks
    SOURCE application_catalog
    SOURCE historical_incidents

MEMORY IncidentHistory
    KEY incident.id

CALL ServiceManagement.create_ticket
    title = "Automation candidate"
```

### 1. Run the default sample (no pause)

```bash
ppl run examples/enterprise_automation.ppl
```

**Input (CLI default):** same repeated DB-pool incident as `incident.ppl`.  
**Output:** `"DATABASE"`.  
**Side effect:** a line in `.ppl/tickets.jsonl`. Human approval is **SKIPPED** (local confidence ≥ 0.85).

```bash
ppl trace examples/enterprise_automation.ppl
```

You should see `IF … else`, `CALL … create_ticket`, `RETURN … DATABASE`.

### 2. Force the human gate

Save `needs-approval.json` with a vague description (e.g. `"Odd intermittent glitch"`). Then either:

**bash — auto-approve**

```bash
export PPL_HUMAN_DECISION=APPROVE
ppl run examples/enterprise_automation.ppl --input needs-approval.json
```

**PowerShell**

```powershell
$env:PPL_HUMAN_DECISION = "APPROVE"
ppl run examples/enterprise_automation.ppl --input needs-approval.json
```

**Or pause / resume**

```bash
ppl run examples/enterprise_automation.ppl --input needs-approval.json --execution-id ticket-1
ppl approve ticket-1 APPROVE --resume --file examples/enterprise_automation.ppl
```

If you are at an interactive `Decision>` prompt, type `APPROVE`. Exit status **2** means `WAITING`, not a crash.

`SOURCE` names map to files under `examples/knowledge/`. `create_ticket` is a fail-closed builtin.

**Tip:** Delete `.ppl/` for a clean memory/ticket/execution slate. Transcripts: [EXAMPLES.md](EXAMPLES.md) §4.

### What this lesson taught

`KNOWLEDGE` / `SOURCE`, `MEMORY`, `TOOL` / `CALL`, human-in-the-loop, builtin tools.

---

## Lesson 5 — Durable runs and workers

**Goal:** See that executions are files you can name, and that `--workers` is a local process pool.

Executions persist as `.ppl/executions/<id>.json`.

```bash
ppl run examples/hello_world.ppl --execution-id hello-1
ppl run examples/hello_world.ppl --workers 2
```

`PARALLEL` branches may overlap. `--workers N` starts a local process pool sharing the file store — not a remote cluster.

Optional long-running worker (stop with Ctrl+C):

```bash
ppl worker --file examples/hello_world.ppl
```

See [PPL_0.9.md](PPL_0.9.md) for WAIT predicates, JOIN, and the store layout.

### What this lesson taught

`--execution-id`, file-backed store, local workers vs. a distributed cluster.

---

## Lesson 6 — Switch providers without changing source

**Goal:** Point the same `.ppl` file at a live model using only environment (or `ppl.providers.json`).

```bash
export PPL_AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=...
ppl run examples/hello_world.ppl
```

**PowerShell:** `$env:PPL_AI_PROVIDER = "anthropic"`.

The `.ppl` file does not mention Anthropic (or any vendor). Unset `PPL_AI_PROVIDER` to return to the local adapter.

Skip this lesson until Lessons 1–4 feel comfortable. Details: [REAL_AI_RUNTIME.md](REAL_AI_RUNTIME.md).

### What this lesson taught

Provider-neutral source; configuration lives outside the program.

---

## After the tutorial

- [VISUAL_EDITOR.md](VISUAL_EDITOR.md) — browser editor, run/trace, AI coding assistant
- [EXAMPLES.md](EXAMPLES.md) — more programs and first-app ideas
- [SPEC.md](SPEC.md) — semantics
- [PPL_0.10.md](PPL_0.10.md) — adapter registry
- [GETTING_STARTED.md](GETTING_STARTED.md) — CLI, env vars, troubleshooting
