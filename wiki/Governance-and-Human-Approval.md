# Governance and Human Approval

PPL 0.4+ governance is **runtime-enforced** — not instructions embedded in prompts.

## GUARD

```text
GUARD ProductionSafety
    NEVER execute production changes
        without authorization
```

Declares safety policies evaluated by the runtime before risky operations proceed.

## AUTHORIZATION

```text
AUTHORIZATION production_change
    REQUIRES production.write
```

Names a permission requirement. The runtime checks authorization context (not model output).

## BUDGET

```text
BUDGET
    max_cost: 0.10
    max_latency: 5000ms
    max_steps: 10
```

Limits cost, latency, and step count for an execution.

## ENVIRONMENT

Declares deployment context (e.g. `production`, `staging`) for policy evaluation.

## HUMAN_APPROVAL

```text
IF RiskAnalyzer.confidence < 0.90
    HUMAN_APPROVAL
```

Or with explicit question/options:

```text
HUMAN_APPROVAL
    QUESTION:
        validate the analysis before continuing
    OPTIONS:
        APPROVE
        REJECT
```

### State transition

```text
RUNNING → WAITING → RESUMING → RUNNING
```

The decision is recorded with:

- execution ID
- actor (when available)
- timestamp
- question and options
- chosen value

### CLI workflow

```bash
ppl run app.ppl --execution-id demo
# Interactive TTY:
#   HUMAN_APPROVAL [demo]
#   Question: ...
#   Decision>

ppl approve demo APPROVE --resume --file app.ppl
```

### Non-interactive / CI

```bash
export PPL_HUMAN_DECISION=APPROVE
ppl run app.ppl
```

Exit code **2** means `WAITING` (not a crash).

### Resume without auto-continue

```bash
ppl approve demo APPROVE --file app.ppl
ppl resume demo --file app.ppl
```

Always pass `--file` if the stored execution lacks `program_path`.

## Example: governed change

`examples/governed_change.ppl` combines `GUARD`, `AUTHORIZATION`, `BUDGET`, and confidence-gated approval.

```bash
ppl run examples/governed_change.ppl
# → "APPROVED" (local adapter: high confidence, no pause)
```

## Governance + tools

Before connecting write-capable enterprise tools:

1. Add `GUARD` and `HUMAN_APPROVAL` gates
2. Set `BUDGET` limits
3. Evaluate cognitive behavior on representative inputs
4. Use `ppl trace` to verify gate paths

---

**See also:** [[Runtime and Execution Graph]] · [[Examples]]
