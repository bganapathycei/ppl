# PPL examples

These examples are ordered from beginner to advanced. Current runtime: **0.10**.

**Before you start:** install from the repo root (`python -m pip install -e .`) and complete [GETTING_STARTED.md](GETTING_STARTED.md) through the first `ppl run`. The default `local` adapter needs no API key. Run every command from the repository root.

---

## 1. Hello AI

`examples/hello_world.ppl` is the smallest useful PPL application.

```text
APP -> INPUT -> AGENT -> CLASSIFY -> WORKFLOW
```

```bash
ppl check examples/hello_world.ppl
ppl run examples/hello_world.ppl
ppl trace examples/hello_world.ppl
```

**Expected local result:** `"GREETING"`.

What to notice: `RETURN Classifier.category` reads the agent field, not a string literal. On the local adapter this program always returns `"GREETING"` (see Getting Started Step 6).

---

## 2. Incident advisor

`examples/incident.ppl` runs two agents in a deterministic workflow: classification, extraction, reasoning, confidence, and `IF` on a score.

```text
RUN Analyzer
RUN AutomationAdvisor
IF score >= threshold
    RETURN decision
```

```bash
ppl run examples/incident.ppl
ppl run examples/incident.ppl --input examples/incident.json
```

**Expected local result:** `"AUTOMATE"`.

Try changing `examples/incident.json` and re-running so you can see `"KEEP_HUMAN"` when the local score drops. Walkthrough: [TUTORIAL.md](TUTORIAL.md) Lesson 2.

---

## 3. Governed change

`examples/governed_change.ppl` introduces 0.4 governance that the 0.9+ runtime still enforces:

- `GUARD`
- `AUTHORIZATION`
- `BUDGET`
- confidence-based `HUMAN_APPROVAL`

Risky actions are governed by the runtime, not by instructions inside a prompt.

```bash
ppl run examples/governed_change.ppl
```

**Expected local result:** `"APPROVED"` (high local confidence, no pause).

---

## 4. Enterprise automation

`examples/enterprise_automation.ppl` exercises knowledge files, persistent memory, tools, and optional human approval. Sample documents live in `examples/knowledge/`.

```text
KNOWLEDGE + MEMORY -> AGENT -> CALL create_ticket -> RETURN
```

The local adapter often returns analyzer `confidence` below `0.85`, so this program **pauses** unless you approve:

```bash
# bash
export PPL_HUMAN_DECISION=APPROVE
ppl run examples/enterprise_automation.ppl
```

```powershell
# PowerShell
$env:PPL_HUMAN_DECISION = "APPROVE"
ppl run examples/enterprise_automation.ppl
```

Or: `ppl run … --execution-id demo` then `ppl approve demo APPROVE --resume --file examples/enterprise_automation.ppl`.

A 0.3-era snapshot of the same program is in `examples/enterprise_automation_v03.md`; the live source is the `.ppl` file.

---

## 5. Real-AI incident (same language, live models)

`examples/real_ai_incident.ppl` is the incident pattern with explicit `MODEL_POLICY` model ids. It still does not name a vendor API. Point the runtime at a provider:

```bash
export PPL_AI_PROVIDER=openai
export OPENAI_API_KEY=...
ppl run examples/real_ai_incident.ppl
```

See [REAL_AI_RUNTIME.md](REAL_AI_RUNTIME.md). Skip this example until hello world and incident run cleanly on `local`.

---

## 6. Recommended learning path

1. Follow [GETTING_STARTED.md](GETTING_STARTED.md) Steps 1–12 (install through bundled examples).
2. Run `hello_world.ppl`, then `ppl compile` / `ppl trace`.
3. Run `incident.ppl` with and without `examples/incident.json`.
4. Work through [TUTORIAL.md](TUTORIAL.md) Lessons 1–6.
5. Study `governed_change.ppl` and `enterprise_automation.ppl` (including pause/resume).
6. Read [PPL_0.9.md](PPL_0.9.md) and [PPL_0.10.md](PPL_0.10.md).
7. Read [SPEC.md](SPEC.md).
8. `ppl init my-app` and build a small **read-only** workflow before adding write-capable tools.

---

## 7. Example application ideas

Good first PPL applications:

- IT incident triage
- QA defect classification
- invoice document extraction
- customer email routing
- contract clause analysis
- knowledge-grounded support recommendations

Prefer recommendation-only behavior at first. Add write actions only after cognitive behavior is evaluated and guards/approvals are in place.
