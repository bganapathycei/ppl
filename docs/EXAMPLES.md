# PPL examples — commands, inputs, and outputs

Current runtime: **0.10**. Install from the repo root (`python -m pip install -e .`), activate your venv, and run every command from the **repository root**.

Unless noted, these sessions use the default **`local`** adapter (no API key, no live LLM). Cognitive steps still run; they use in-process heuristics. `[D]` = deterministic, `[C]` = cognitive, `[H]` = human.

---

## How to read each example

Every section shows:

1. **What the program teaches**
2. **Command** you type
3. **Input** the runtime uses (CLI default or `--input` file)
4. **Output** you should see
5. **What happened** on the execution graph

---

## 1. Hello world — `examples/hello_world.ppl`

Deterministic script (no API key):

```bash
ppl run examples/hello_world.ppl --stdio
```

**Output:** prints `Hello, world` and returns `"Hello, world"`.

## 2. Hello AI — `examples/hello_world_ai.ppl`

**Teaches:** `APP`, `INPUT`, `AGENT`, `CLASSIFY`, `WORKFLOW`, `RETURN` field paths.

### Check (compile only — no cognitive call)

```bash
ppl check examples/hello_world.ppl
```

**Output:**

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

### Run (default sample input)

```bash
ppl run examples/hello_world.ppl
```

**Input (injected by the CLI because `INPUT request` exists):**

```json
{
  "request": {
    "text": "hello there",
    "done": true
  }
}
```

**Output:**

```json
"GREETING"
```

**What happened**

| Step | Class | Detail |
|---|---|---|
| `RECEIVE request` | D | Binds the JSON above |
| `RUN Classifier` | D | Starts the agent |
| `CLASSIFY` | C | Local adapter picks a category (`GREETING` for this program) |
| `RETURN Classifier.category` | D | Prints the agent field — not the literal string `"Classifier.category"` |

### Trace (same run, with graph)

```bash
ppl trace examples/hello_world.ppl
```

**Output (shape):**

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

### Custom input file

Create `my-hello.json`:

```json
{
  "request": {
    "text": "what time is it?"
  }
}
```

```bash
ppl run examples/hello_world.ppl --input my-hello.json
```

**Local output:** still `"GREETING"`. The local adapter does not score greeting vs question keywords; with a live provider the category can follow the sentence.

---

## 2. Incident advisor — `examples/incident.ppl`

**Teaches:** two agents, `MODEL_POLICY`, `EXTRACT` / `REASON`, `IF` / `ELSE IF` / `ELSE`.

### Run with CLI default input

```bash
ppl run examples/incident.ppl
```

**Input (injected):**

```json
{
  "incident": {
    "description": "Repeated database connection pool failure",
    "application": "Order Management",
    "priority": "P2",
    "id": "INC-1001"
  }
}
```

**Output:**

```json
"AUTOMATE"
```

**What happened**

1. `Analyzer` classifies as `DATABASE`, extracts root cause/resolution, reasons about repetition.
2. `AutomationAdvisor` scores automation (local adapter → **86** when repetitive).
3. Workflow: `IF score >= 80` → `RETURN "AUTOMATE"`.

### Run with the sample file

`examples/incident.json`:

```json
{
  "incident": {
    "description": "Users report a repeated database connection pool failure",
    "application": "Order Management",
    "priority": "P2"
  }
}
```

```bash
ppl run examples/incident.ppl --input examples/incident.json
```

**Output:**

```json
"AUTOMATE"
```

### Experiment — force a human-kept decision

Save as `keep-human.json`:

```json
{
  "incident": {
    "description": "One-off laptop screen flicker",
    "application": "Laptop",
    "priority": "P4",
    "id": "INC-9"
  }
}
```

```bash
ppl run examples/incident.ppl --input keep-human.json
```

**Local output:**

```json
"KEEP_HUMAN"
```

**Why:** no “repeated” / database keywords → local automation **score 42** → `ELSE` branch.

### Trace

```bash
ppl trace examples/incident.ppl
```

Look for `[C]` lines (`CLASSIFY`, `EXTRACT`, `REASON`) and the final `RETURN` / `IF` outcome.

---

## 3. Governed change — `examples/governed_change.ppl`

**Teaches:** `GUARD`, `AUTHORIZATION`, `BUDGET`, confidence-gated `HUMAN_APPROVAL`.

```bash
ppl run examples/governed_change.ppl
```

**Input (injected):**

```json
{
  "change": {
    "description": "Increase database connection pool in production",
    "environment": "production",
    "risk": 3
  }
}
```

**Output:**

```json
"APPROVED"
```

**What happened**

1. `RiskAnalyzer` (local) returns `safe: true`, `confidence: 0.92`.
2. `IF confidence < 0.90` is **false**, so `HUMAN_APPROVAL` is skipped.
3. `ELSE IF safe == TRUE` → `"APPROVED"`.

Guards/budgets are runtime metadata; they are not “prompt text” to the model.

Named execution (same happy path):

```bash
ppl run examples/governed_change.ppl --execution-id change-1
```

---

## 4. Enterprise automation — `examples/enterprise_automation.ppl`

**Teaches:** `KNOWLEDGE` / `SOURCE`, `MEMORY`, `TOOL` / `CALL`, optional human gate, ticket builtin.

Knowledge files: `examples/knowledge/*.md`.

### Run with CLI default input

```bash
ppl run examples/enterprise_automation.ppl
```

**Input (injected):**

```json
{
  "incident": {
    "description": "Repeated database connection pool failure",
    "application": "Order Management",
    "priority": "P2",
    "id": "INC-1001"
  }
}
```

**Output:**

```json
"DATABASE"
```

**What happened**

| Step | Class | Detail |
|---|---|---|
| `RECEIVE` | D | Binds incident JSON |
| `RUN Analyzer` | D / C | Loads knowledge + memory; `CLASSIFY` → `DATABASE`; extract/reason |
| `IF confidence < 0.85` | D | Local confidence is high enough → **else** (human node **SKIPPED**) |
| `CALL create_ticket` | D | Appends a line to `.ppl/tickets.jsonl` |
| `RETURN Analyzer.category` | D | `"DATABASE"` |

### Trace excerpt

```bash
ppl trace examples/enterprise_automation.ppl
```

```text
Status: SUCCEEDED
...
CLASSIFY                 [C] ...
EXTRACT                  [C] ...
REASON                   [C] ...
IF                       [D] else
CALL ServiceManagement.create_ticket [D] ok
RETURN                   [D] DATABASE

Result:
"DATABASE"
```

### Demo human approval (low-confidence local path)

Save as `needs-approval.json`:

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

**Interactive TTY:**

```bash
ppl run examples/enterprise_automation.ppl --input needs-approval.json --execution-id demo
```

You may see:

```text
HUMAN_APPROVAL [demo]
Question: validate the analysis before continuing
Options: APPROVE, REJECT
Decision>
```

Type `APPROVE`. Final result is a category string (often `"ACCESS"` locally).

**Non-interactive / CI:**

```bash
# bash
export PPL_HUMAN_DECISION=APPROVE
ppl run examples/enterprise_automation.ppl --input needs-approval.json
```

```powershell
# PowerShell
$env:PPL_HUMAN_DECISION = "APPROVE"
ppl run examples/enterprise_automation.ppl --input needs-approval.json
```

**Pause then resume** (no env var, non-TTY exits with status **2** = `WAITING`):

```bash
ppl run examples/enterprise_automation.ppl --input needs-approval.json --execution-id demo
ppl approve demo APPROVE --resume --file examples/enterprise_automation.ppl
```

---

## 5. Real-AI incident — `examples/real_ai_incident.ppl`

**Teaches:** same language, live model via env (source stays vendor-free).

```bash
# bash
export PPL_AI_PROVIDER=openai
export OPENAI_API_KEY=...
export PPL_AI_MODEL=gpt-4.1-mini
ppl run examples/real_ai_incident.ppl --input examples/incident.json
```

```powershell
$env:PPL_AI_PROVIDER = "openai"
$env:OPENAI_API_KEY = "..."
$env:PPL_AI_MODEL = "gpt-4.1-mini"
ppl run examples/real_ai_incident.ppl --input examples/incident.json
```

**Output:** a classification string from the live model (e.g. `"DATABASE"`). Category can vary by model.

Unset `PPL_AI_PROVIDER` to return to local. Details: [REAL_AI_RUNTIME.md](REAL_AI_RUNTIME.md).

---

## 6. Quick reference — local defaults

| Program | Command | Default / sample input theme | Local output |
|---|---|---|---|
| `hello_world.ppl` | `ppl run examples/hello_world.ppl` | `"hello there"` | `"GREETING"` |
| `incident.ppl` | `ppl run examples/incident.ppl` | repeated DB pool | `"AUTOMATE"` |
| `incident.ppl` | `… --input keep-human.json` | one-off flicker | `"KEEP_HUMAN"` |
| `governed_change.ppl` | `ppl run examples/governed_change.ppl` | production pool change | `"APPROVED"` |
| `enterprise_automation.ppl` | `ppl run examples/enterprise_automation.ppl` | repeated DB pool | `"DATABASE"` (+ ticket file) |

---

## 7. Learning path

1. [GETTING_STARTED.md](GETTING_STARTED.md) Steps 1–6, then this file §1–2.
2. [TUTORIAL.md](TUTORIAL.md) Lessons 1–4.
3. §3–4 here (governance + enterprise + pause demo).
4. [VISUAL_EDITOR.md](VISUAL_EDITOR.md) — optional browser editor with the same examples in the Example menu.
5. [PPL_0.9.md](PPL_0.9.md), [PPL_0.10.md](PPL_0.10.md), [SPEC.md](SPEC.md).
6. `ppl init my-app` and build a **read-only** workflow before write-capable tools.

---

## 8. First-app ideas

- IT incident triage  
- QA defect classification  
- Invoice field extraction  
- Customer email routing  
- Contract clause analysis  
- Knowledge-grounded support recommendations  

Prefer recommendations before autonomous `CALL`s that change external systems.
