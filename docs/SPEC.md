# PPL Language Specification — Draft 0.4

## 1. Purpose

PPL (Prompt Programming Language) is an AI-native, intent-oriented programming language. A PPL application expresses data, deterministic control flow, cognitive operations, enterprise knowledge, memory, tools, human decisions, governance, and evaluation without embedding a model-provider API in application source.

## 2. Execution classes

- **D — Deterministic:** parsing, branching, data movement, validation, arithmetic, state transitions, and ordinary program control.
- **C — Cognitive:** classification, extraction, reasoning, planning, generation, and other model-backed operations.
- **H — Human:** approval, review, escalation, correction, and other human-in-the-loop operations.

## 3. Compilation model

```text
Source -> AST -> Semantic Validation -> PIR -> Runtime
                                      |
                                      +-> Policy / Guard evaluation
                                      +-> AI Gateway
                                      +-> Knowledge / Memory / Tools
                                      +-> Human interface
```

## 4. 0.4 governance surface

### GUARD

Declares a non-negotiable runtime constraint.

```text
GUARD ProductionChange
    NEVER execute production changes
        without authorization
```

A guard is a runtime policy, not a model instruction. The runtime MUST evaluate applicable guards before executing a protected action.

### AUTHORIZATION

Defines the capability scope required for an operation.

```text
AUTHORIZATION production_change
    REQUIRES production.write
```

The runtime SHOULD fail closed when authorization cannot be established.

### ENVIRONMENT

Allows policies to distinguish development, test, staging, and production execution.

```text
ENVIRONMENT production
    REQUIRES production.write
```

## 5. Human approval

`HUMAN_APPROVAL` is a first-class execution state.

```text
HUMAN_APPROVAL
    QUESTION:
        approve the proposed production change
    OPTIONS:
        APPROVE
        REJECT
```

State model:

```text
RUNNING -> WAITING_FOR_HUMAN -> RESUMED | REJECTED | EXPIRED
```

The decision MUST be attributable to execution ID, actor, timestamp, question, options, and selected value.

## 6. Evaluation surface

### TEST

Defines executable expectations over a representative input.

```text
TEST IncidentAdvisor
    GIVEN incident.description = "database outage"
    EXPECT Analyzer.category = DATABASE
```

### EVALUATION

Defines dataset-level quality requirements.

```text
EVALUATION IncidentAdvisor
    DATASET incident_test_set
    METRIC classification_accuracy >= 0.95
    METRIC unsupported_claim_rate <= 0.02
```

Evaluation is part of the application lifecycle and SHOULD run before production deployment.

## 7. Provenance

Every cognitive execution SHOULD retain:

- execution ID
- program version
- source/prompt version
- model and model version
- policy version
- knowledge sources used
- memory reads/writes
- tool calls
- human decisions
- validation result
- outcome

This creates an auditable chain from source intent to observed result.

## 8. Runtime budgets

0.4 introduces the concept of execution budgets:

```text
BUDGET
    max_cost: 0.10
    max_latency: 5000ms
    max_steps: 25
```

A runtime MUST surface a budget violation rather than silently exceeding a declared hard limit.

## 9. AI debugger and trace

The runtime SHOULD expose a structured trace for every step:

```text
STEP 04
OPERATION: REASON
TYPE: C
MODEL: reasoning-default
LATENCY: 1240ms
TOKENS: 723
COST: 0.0042
CONFIDENCE: 0.91
VALIDATION: PASS
STATUS: SUCCESS
```

The trace is diagnostic data and is not itself application state.

## 10. Structured cognitive output

Cognitive output MUST be schema-validated before being committed to program state.

Supported semantic types include:

```text
TEXT
NUMBER
INTEGER
BOOLEAN
MONEY
PERCENT
ID
CONFIDENCE
CLASSIFICATION
```

`CONFIDENCE` is normalized to `[0,1]`.

## 11. Failure semantics

PPL distinguishes:

- `VALIDATION_ERROR` — output violates the declared schema.
- `AUTHORIZATION_ERROR` — required capability is unavailable.
- `GUARD_VIOLATION` — a protected operation violates policy.
- `TOOL_ERROR` — external capability failed.
- `MODEL_ERROR` — model execution failed.
- `BUDGET_EXCEEDED` — a hard runtime budget was exceeded.
- `HUMAN_REJECTED` — an explicit human decision rejected the operation.

Errors SHOULD be observable and SHOULD NOT be hidden inside model-generated text.

## 12. Design principles

1. Intent over provider API.
2. Deterministic shell around cognitive operations.
3. Cognitive outputs are typed data, not free-form strings.
4. Knowledge, memory, tools, and humans are first-class runtime concepts.
5. Governance is enforced by the runtime, not delegated to prompts.
6. Evaluation is part of programming, not an afterthought.
7. Runtime behavior is observable and attributable.
8. Application source remains portable across model providers.
