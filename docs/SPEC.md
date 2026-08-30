# PPL Language Specification — Draft 0.1

## 1. Purpose

PPL (Prompt Programming Language) is designed to make AI-enabled behavior a first-class part of executable software. A PPL program describes intent and execution semantics without embedding a specific model provider API.

## 2. Execution classes

Every operation belongs to an execution class:

- **D — Deterministic:** parsing, branching, data movement, validation, and ordinary program control.
- **C — Cognitive:** classification, extraction, reasoning, generation, or other model-backed operations.
- **H — Human:** approval, escalation, review, or other human-in-the-loop operations planned for later releases.

## 3. Compilation model

```text
Source -> AST -> Semantic Validation -> PIR -> Runtime
```

PIR is intentionally provider-neutral. A runtime may select models, tools, policies, and execution backends without changing PPL source.

## 4. Core grammar concepts

### APP
Defines the application/program name.

### INPUT
Defines an input object and its fields.

### AGENT
Defines a named cognitive worker with an optional input and a sequence of cognitive operations.

### CLASSIFY
Maps a value into one of a declared set of categories.

### EXTRACT
Requests named fields from available context.

### REASON
Expresses a natural-language reasoning objective. The text is semantic source code, not a direct provider prompt.

### OUTPUT
Declares the values exposed by an agent.

### WORKFLOW
Defines deterministic orchestration.

### RECEIVE / RUN
Receive external input and execute an agent.

### IF / ELSE IF / ELSE
Deterministic control flow over resolved runtime values.

### RETURN
Terminates the workflow with a value.

## 5. Design principles

1. **Intent over provider API.** PPL source must not depend on a model vendor.
2. **Deterministic shell, cognitive core.** Control flow remains inspectable and deterministic around model operations.
3. **Typed cognitive output.** Future versions should make cognitive results schema-bound and validated.
4. **Runtime governance.** Model selection, policies, budgets, safety controls, and telemetry belong in the runtime.
5. **Observable execution.** Every cognitive operation should be traceable for latency, cost, model, confidence, and outcome.
6. **Composable agents.** Agents should be independently testable and orchestratable.

## 6. Planned 0.2 semantics

- `MODEL_POLICY`
- explicit cognitive output schemas
- model/provider abstraction
- structured result validation
- confidence and uncertainty semantics
- retry/fallback policies
- token/cost/latency telemetry

## 7. Non-goals for 0.1

PPL 0.1 is not a production agent platform. The local cognitive engine is deliberately a deterministic stand-in used to prove language and runtime separation.
