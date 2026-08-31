# Language Reference

Draft specification aligned with **PPL 0.10**. For runnable tutorials see [[Getting Started]] and [[Examples]].

## Program structure

```text
APP MyApplication

INPUT request
    text: TEXT

MODEL_POLICY Default
    reasoning: reasoning-default
    classification: classification-default

KNOWLEDGE Docs
    SOURCE runbooks

MEMORY History
    KEY request.id

TOOL ITSM
    ACTION create_ticket
    INPUT
        title: TEXT
    OUTPUT
        ticket_id: ID

GUARD Safety
    NEVER execute sensitive actions without authorization

AUTHORIZATION prod_change
    REQUIRES production.write

BUDGET
    max_cost: 0.10
    max_steps: 20

AGENT Classifier
    INPUT request
    POLICY Default
    USE KNOWLEDGE Docs
    USE MEMORY History

    CLASSIFY request.text AS
        GREETING
        QUESTION
        OTHER

    EXTRACT
        field_name: TEXT

    REASON
        determine the best next action
        OUTPUT:
            action: TEXT
            confidence: CONFIDENCE

    OUTPUT
        category
        confidence

WORKFLOW Main
    RECEIVE request
    RUN Classifier

    IF Classifier.confidence < 0.90
        HUMAN_APPROVAL
            QUESTION:
                validate before continuing
            OPTIONS:
                APPROVE
                REJECT

    PARALLEL
        RUN AgentA
        RUN AgentB
    JOIN AgentA

    WAIT 1s
    WAIT order.paid
    WAIT file:.ppl/events/paid

    CALL ITSM.create_ticket
        title = "Example"

    RETURN Classifier.category
```

## Keywords by category

### Application

| Keyword | Purpose |
|---|---|
| `APP` | Program name |
| `INPUT` | Structured input schema |
| `MODEL_POLICY` | Model slots, retries, fallback |

### Cognitive (agents)

| Keyword | Purpose |
|---|---|
| `AGENT` | Cognitive worker |
| `CLASSIFY … AS` | Constrained categories |
| `EXTRACT` | Named field extraction |
| `REASON` | Natural-language objective with optional `OUTPUT:` schema |
| `OUTPUT` | Agent-exposed fields |
| `POLICY` | Bind `MODEL_POLICY` |
| `USE KNOWLEDGE` | Attach knowledge source |
| `USE MEMORY` | Attach memory store |

### Orchestration (workflows)

| Keyword | Purpose |
|---|---|
| `WORKFLOW` | Deterministic orchestration block |
| `RECEIVE` | Bind input |
| `RUN` | Execute agent |
| `IF` / `ELSE IF` / `ELSE` | Branching |
| `RETURN` | Workflow result (supports field paths like `Agent.field`) |
| `PARALLEL` | Concurrent branches |
| `JOIN` | Dependency barrier |
| `WAIT` | Suspend (duration, context path, or file) |
| `CHECKPOINT` | Persist resumable state |
| `CALL` | Invoke tool action |
| `HUMAN_APPROVAL` | Human gate |

### Enterprise

| Keyword | Purpose |
|---|---|
| `KNOWLEDGE` / `SOURCE` | File-backed context |
| `MEMORY` | Persistent JSON state |
| `TOOL` / `ACTION` | External capability contract |
| `GUARD` | Safety policy |
| `AUTHORIZATION` | Permission requirement |
| `BUDGET` | Cost/latency/step limits |
| `ENVIRONMENT` | Deployment context |

## Types

Common field types: `TEXT`, `NUMBER`, `INTEGER`, `BOOLEAN`, `CONFIDENCE`, `CLASSIFICATION`, `ID`.

## Compilation model

```text
Source → AST → Semantic Validation → PIR → Execution Graph → Runtime
```

The graph is a **DAG** (acyclic). Each node has a stable ID, operation, dependencies, status, output, and error.

## Runtime states

**Execution:** `CREATED`, `RUNNING`, `WAITING`, `RESUMING`, `SUCCEEDED`, `FAILED`, `CANCELLED`

**Node:** `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `WAITING`, `CHECKPOINTED`, `CANCELLED`

## Design rules

1. Cognitive outputs are **schema-validated** before entering context.
2. `RETURN Agent.field` resolves the field — it is not a string literal.
3. Governance keywords are **runtime-enforced**, not prompt text.
4. Provider selection is **configuration**, not source syntax.

---

**See also:** [[Governance and Human Approval]] · [[Knowledge Memory and Tools]]
