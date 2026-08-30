# PPL Language Specification — Draft 0.2

## 1. Purpose

PPL (Prompt Programming Language) makes AI-enabled behavior a first-class part of executable software. PPL source describes intent and execution semantics without embedding a specific model-provider API.

## 2. Execution classes

- **D — Deterministic:** parsing, branching, data movement, validation, and ordinary program control.
- **C — Cognitive:** classification, extraction, reasoning, generation, or other model-backed operations.
- **H — Human:** approval, escalation, review, and other human-in-the-loop operations planned for a later release.

## 3. Compilation model

```text
Source -> AST -> Semantic Validation -> PIR -> Runtime -> AI Gateway -> Model Adapter
```

PIR is provider-neutral. The runtime selects a model adapter and policy without changing PPL source.

## 4. Model policy

`MODEL_POLICY` defines runtime preferences independently of application logic.

```text
MODEL_POLICY EnterpriseDefault
    reasoning: reasoning-default
    classification: classification-default
    extraction: extraction-default
    max_retries: 2
    fallback: fallback-default
```

An agent may bind a policy:

```text
AGENT Analyzer
    POLICY EnterpriseDefault
```

## 5. Typed cognitive output

Cognitive operations may declare an output schema. Supported 0.2 types include:

- `TEXT`
- `NUMBER`
- `INTEGER`
- `BOOLEAN`
- `CONFIDENCE` — numeric value constrained to 0..1
- `CLASSIFICATION` — text constrained to the declared classification set

Example:

```text
REASON
    determine whether the incident is repetitive
    OUTPUT:
        repetitive: BOOLEAN
        confidence: CONFIDENCE
```

The runtime validates model output before it enters program state.

## 6. AI gateway

PPL does not call a model provider directly. The runtime creates an `AIRequest` and sends it through an `AIGateway` to a `ModelAdapter`.

The adapter returns:

- structured output
- model identifier
- latency
- token counts
- estimated cost
- attempt count

This creates a stable seam for future OpenAI, Anthropic, Google, local-model, or other adapters without changing the language.

## 7. Retry and fallback

The policy supplies `max_retries` and a `fallback` model identifier. The reference runtime records attempt metadata. Production semantics will add failure classification and explicit retry conditions.

## 8. Observability

Every cognitive step should expose enough telemetry to answer:

- What operation ran?
- Which model executed it?
- How long did it take?
- How many tokens were consumed?
- What did it cost?
- How many attempts were required?
- What confidence was returned?
- Did schema validation succeed?

## 9. Design principles

1. **Intent over provider API.** PPL source remains model-provider neutral.
2. **Deterministic shell, cognitive core.** Control flow remains inspectable around model operations.
3. **Typed cognitive output.** AI results are validated before entering runtime state.
4. **Policy-driven model selection.** Model choices are runtime concerns.
5. **Observable execution.** AI behavior is traceable like ordinary program execution.
6. **Composable agents.** Agents remain independently testable and orchestratable.

## 10. Non-goals for 0.2

PPL 0.2 is not yet a production model gateway. The bundled local adapter is deterministic and exists to validate language/runtime boundaries. Production credentials, provider SDKs, distributed execution, persistent memory, knowledge retrieval, tools, and human approval are later milestones.
