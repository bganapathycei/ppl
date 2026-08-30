# PPL Language Specification — Draft 0.3

## 1. Purpose

PPL (Prompt Programming Language) is an AI-native, intent-oriented programming language. A PPL application expresses data, deterministic control flow, cognitive operations, enterprise knowledge, memory, tools, and human decisions without embedding a model-provider API in application source.

## 2. Execution classes

- **D — Deterministic:** parsing, branching, data movement, validation, arithmetic, state transitions, and ordinary program control.
- **C — Cognitive:** classification, extraction, reasoning, planning, generation, and other model-backed operations.
- **H — Human:** approval, review, escalation, correction, and other human-in-the-loop operations.

## 3. Compilation model

```text
Source -> AST -> Semantic Validation -> PIR -> Runtime
```

PIR is provider-neutral. The runtime selects model adapters, knowledge providers, memory stores, tool adapters, and human interfaces.

## 4. 0.3 language surface

### APP
Defines the application.

### INPUT
Defines an input object and typed fields.

### MODEL_POLICY
Defines provider-neutral routing and execution preferences.

```text
MODEL_POLICY EnterpriseDefault
    reasoning: reasoning-default
    classification: classification-default
    extraction: extraction-default
    max_retries: 2
    fallback: fallback-default
```

### KNOWLEDGE
Declares external authoritative context sources.

```text
KNOWLEDGE ITOperations
    SOURCE incident_history
    SOURCE runbooks
    SOURCE architecture_documents
```

### MEMORY
Declares application-owned historical or stateful information.

```text
MEMORY IncidentHistory
    KEY incident.id
    READ incidents
    WRITE outcomes
```

### TOOL
Declares an executable external capability. The runtime owns authentication, transport, retries, and connector details.

```text
TOOL ServiceManagement
    ACTION create_ticket
    INPUT
        title: TEXT
        description: TEXT
        priority: TEXT
    OUTPUT
        ticket_id: ID
```

### AGENT
Defines a named cognitive worker.

```text
AGENT Analyzer
    USE KNOWLEDGE ITOperations
    USE MEMORY IncidentHistory
    POLICY EnterpriseDefault
```

### CLASSIFY
Constrains a cognitive result to a declared set of categories and produces a confidence value.

### EXTRACT
Produces schema-bound fields from available context.

### REASON
Defines a natural-language reasoning objective. Optional `OUTPUT:` entries inside `REASON` define the result schema.

```text
REASON
    determine whether the incident is repetitive
    OUTPUT:
        repetitive: BOOLEAN
        confidence: CONFIDENCE
        evidence: TEXT
```

### CALL
Invokes a declared tool action. Tool calls are deterministic at the program-control level even when a cognitive agent chooses the arguments.

### HUMAN_APPROVAL
Suspends execution until an authorized human decision is received.

```text
HUMAN_APPROVAL
    QUESTION:
        approve the proposed production change
    OPTIONS:
        APPROVE
        REJECT
```

### WORKFLOW
Defines orchestration over deterministic, cognitive, tool, and human operations.

### RECEIVE / RUN / IF / ELSE IF / ELSE / RETURN
Core workflow control constructs.

## 5. Knowledge semantics

Knowledge sources are external context, not mutable application variables. A cognitive operation may declare one or more knowledge scopes. The runtime is responsible for retrieval, ranking, context assembly, and provenance.

Every production knowledge provider SHOULD expose provenance metadata including source identifier and retrieval location.

## 6. Memory semantics

Memory is persistent application state and is distinct from knowledge:

- **Knowledge** = external authoritative information.
- **Memory** = application-owned historical or stateful information.

Memory reads and writes are observable and should be explicit.

## 7. Tool semantics

Tools are typed capabilities. Tool contracts define inputs and outputs; connector implementation is outside PPL source. Tool execution failures are surfaced as typed runtime errors rather than silently converted into cognitive responses.

## 8. Human semantics

`HUMAN_APPROVAL` is a first-class execution state.

```text
RUNNING -> WAITING_FOR_HUMAN -> RESUMED | REJECTED | EXPIRED
```

Human decisions must be attributable to an execution context.

## 9. Structured cognitive output

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

## 10. Model policy semantics

PPL source describes workload intent, not vendor APIs. `MODEL_POLICY` can specify preferred adapters, retries, fallbacks, and optimization objectives. A runtime MAY choose a different concrete model when policy permits.

The effective model and policy version MUST be traceable for each cognitive execution.

## 11. Execution telemetry

The runtime should record, where available:

- operation type
- model/provider
- model version
- policy version
- input/output token counts
- latency
- retry count
- fallback usage
- cost estimate
- confidence
- validation result
- knowledge provenance
- tool execution result
- human decision metadata

## 12. Security and governance direction

0.3 introduces the semantic building blocks for governed enterprise execution. `GUARD`, authorization scopes, environment controls, and policy enforcement remain planned for the next release.

## 13. Design principles

1. Intent over provider API.
2. Deterministic shell around cognitive operations.
3. Cognitive outputs are typed data, not free-form strings.
4. Knowledge, memory, tools, and humans are first-class runtime concepts.
5. Runtime behavior is observable and attributable.
6. Application source remains portable across model providers.
