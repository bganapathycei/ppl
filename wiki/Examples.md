# Examples

All commands from the **repository root** with the default **`local`** adapter (no API key).

`[D]` = deterministic · `[C]` = cognitive · `[H]` = human

---

## 1. Hello AI — `examples/hello_world.ppl`

**Teaches:** `APP`, `INPUT`, `AGENT`, `CLASSIFY`, `WORKFLOW`, `RETURN` field paths.

```bash
ppl check examples/hello_world.ppl
ppl run examples/hello_world.ppl
```

**Input (CLI default):**

```json
{"request": {"text": "hello there", "done": true}}
```

**Output:** `"GREETING"`

| Step | Class | What happened |
|---|---|---|
| `RECEIVE` | D | Binds input |
| `RUN Classifier` | D | Starts agent |
| `CLASSIFY` | C | Local adapter → category |
| `RETURN Classifier.category` | D | Field path, not literal string |

```bash
ppl trace examples/hello_world.ppl
```

Shows execution graph nodes and `[C]` cognitive steps.

---

## 2. Incident advisor — `examples/incident.ppl`

**Teaches:** two agents, `MODEL_POLICY`, `IF` branching.

```bash
ppl run examples/incident.ppl
```

**Input (CLI default):** repeated DB pool incident (`INC-1001`)

**Output:** `"AUTOMATE"`

```bash
ppl run examples/incident.ppl --input examples/incident.json
```

Still `"AUTOMATE"` — description contains "database connection pool" and "repeated".

**Experiment — lower automation score:**

```json
{"incident": {"description": "One-off laptop screen flicker", "application": "Laptop", "priority": "P4", "id": "INC-9"}}
```

```bash
ppl run examples/incident.ppl --input keep-human.json
```

**Output:** `"KEEP_HUMAN"`

---

## 3. Governed change — `examples/governed_change.ppl`

**Teaches:** `GUARD`, `AUTHORIZATION`, `BUDGET`, `HUMAN_APPROVAL`.

```bash
ppl run examples/governed_change.ppl
```

**Output:** `"APPROVED"`

Local adapter returns `confidence: 0.92` → human gate skipped.

---

## 4. Enterprise automation — `examples/enterprise_automation.ppl`

**Teaches:** `KNOWLEDGE`, `MEMORY`, `CALL create_ticket`.

Knowledge files: `examples/knowledge/*.md`

```bash
ppl run examples/enterprise_automation.ppl
```

**Output:** `"DATABASE"`  
**Side effect:** line appended to `.ppl/tickets.jsonl`

### Practice human approval

Use a vague incident description so local confidence drops below `0.85`:

```json
{"incident": {"description": "Odd intermittent glitch", "application": "Portal", "priority": "P3", "id": "INC-77"}}
```

```bash
# CI / non-interactive
export PPL_HUMAN_DECISION=APPROVE
ppl run examples/enterprise_automation.ppl --input needs-approval.json

# Interactive pause/resume
ppl run examples/enterprise_automation.ppl --input needs-approval.json --execution-id demo
ppl approve demo APPROVE --resume --file examples/enterprise_automation.ppl
```

---

## 5. Real-AI incident — `examples/real_ai_incident.ppl`

Same language; live model via env only:

```bash
export PPL_AI_PROVIDER=openai
export OPENAI_API_KEY=...
ppl run examples/real_ai_incident.ppl --input examples/incident.json
```

See [[Providers and LLM Configuration]].

---

## Quick reference table

| Program | Command | Local output |
|---|---|---|
| `hello_world.ppl` | `ppl run examples/hello_world.ppl` | `"GREETING"` |
| `incident.ppl` | `ppl run examples/incident.ppl` | `"AUTOMATE"` |
| `incident.ppl` | `… --input keep-human.json` | `"KEEP_HUMAN"` |
| `governed_change.ppl` | `ppl run examples/governed_change.ppl` | `"APPROVED"` |
| `enterprise_automation.ppl` | `ppl run examples/enterprise_automation.ppl` | `"DATABASE"` |

The same four programs are bundled in the visual editor **Example** menu. Run them in the browser with `python editor/serve.py` — see [[Visual Editor]].

---

**See also:** [[Visual Editor]] · [[Getting Started]] · [[Language Reference]]
