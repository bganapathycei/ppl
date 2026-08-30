# PPL 0.4 — Getting Started

Welcome to PPL (Prompt Programming Language).

PPL is an intent-oriented language for building AI-native software. A PPL program combines deterministic logic with cognitive operations such as classification, extraction, and reasoning.

## 1. Mental model

Think of PPL as:

```text
Intent -> PPL source -> AST -> PIR -> Runtime
                                      |
                       +--------------+--------------+
                       |              |              |
                 Deterministic   Cognitive       Human
```

You describe **what the application should do**. The runtime decides how model-backed operations are executed.

## 2. Your first program

Create `hello.ppl`:

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

Run:

```bash
ppl check hello.ppl
ppl compile hello.ppl
ppl run hello.ppl
ppl trace hello.ppl
```

## 3. The core building blocks

### APP
Names your program.

```text
APP OrderAssistant
```

### INPUT
Defines structured data entering the program.

```text
INPUT order
    id: ID
    amount: NUMBER
```

### AGENT
Defines a cognitive worker.

```text
AGENT RiskAnalyzer
    INPUT order
```

### CLASSIFY
Constrains an AI decision to declared categories.

```text
CLASSIFY order AS
    LOW
    MEDIUM
    HIGH
```

### EXTRACT
Requests named fields from context.

```text
EXTRACT
    customer_name
    contract_number
```

### REASON
Expresses a reasoning objective in natural language.

```text
REASON
    determine whether this order presents unusual risk
```

### OUTPUT
Defines values an agent exposes.

```text
OUTPUT
    risk
    confidence
```

### WORKFLOW
Orchestrates deterministic execution.

```text
WORKFLOW Main
    RECEIVE order
    RUN RiskAnalyzer
```

## 4. Execution classes

Every operation belongs conceptually to one of three classes:

- **D — Deterministic:** branching, validation, data movement, ordinary control flow.
- **C — Cognitive:** model-backed reasoning, classification, extraction, generation.
- **H — Human:** approval, review, escalation.

This separation is one of PPL's central design principles.

## 5. Build an AI-native application

A typical application follows this pattern:

```text
APP
  |
  +-- INPUT
  |
  +-- KNOWLEDGE
  |
  +-- MEMORY
  |
  +-- AGENT
  |     +-- CLASSIFY
  |     +-- EXTRACT
  |     +-- REASON
  |
  +-- TOOL
  |
  +-- WORKFLOW
        +-- RUN
        +-- IF
        +-- HUMAN_APPROVAL
```

## 6. Knowledge

Knowledge represents authoritative external context.

```text
KNOWLEDGE ITPolicy
    SOURCE policy_documents
    SOURCE operational_runbooks
```

Use it from an agent:

```text
AGENT Advisor
    USE KNOWLEDGE ITPolicy

    REASON
        recommend the compliant remediation
```

## 7. Memory

Memory represents application history or state.

```text
MEMORY IncidentHistory
```

An agent can use memory to reason over previous executions or outcomes.

## 8. Tools

Tools represent executable external capabilities.

```text
TOOL ITSM
    ACTION create_ticket
        title: TEXT
        description: TEXT
        priority: TEXT
```

The language should remain independent of the underlying REST API, SDK, or connector.

## 9. Human approval

Use human decisions when confidence or risk requires explicit intervention.

```text
IF confidence < 0.90
    HUMAN_APPROVAL
```

The runtime should represent this as an explicit waiting state rather than hiding the interaction inside a prompt.

## 10. Debugging

Use:

```bash
ppl trace app.ppl
```

to inspect the execution graph and cognitive steps.

For every cognitive operation, aim to expose:

- operation
- model
- input/output schema
- latency
- token usage
- estimated cost
- confidence
- validation result
- retry/fallback behavior

## 11. Testing

A good PPL application should test both deterministic behavior and cognitive quality.

Deterministic example:

```text
EXPECT
    score >= 80
```

Cognitive evaluation should eventually use representative datasets and metrics such as classification accuracy, extraction accuracy, unsupported-claim rate, and human override rate.

## 12. Development workflow

Recommended loop:

```text
1. Write intent
2. Run `ppl check`
3. Inspect `ppl compile`
4. Run against representative inputs
5. Inspect `ppl trace`
6. Add tests/evaluations
7. Add guards for risky actions
8. Connect real models/tools
9. Deploy only after evaluation passes
```

## 13. Recommended first project

Start with a bounded business process such as incident triage, invoice classification, customer email routing, or QA defect analysis.

Avoid autonomous production actions in your first application. Begin with analysis and recommendations, then introduce tools and human approval after the behavior is measurable.

## 14. Where to go next

Read:

- `docs/SPEC.md` for language semantics
- `examples/` for complete programs
- `src/ppl/` for the reference runtime

PPL is an experimental language. Expect the syntax and runtime contracts to evolve until the 1.0 specification is frozen.
