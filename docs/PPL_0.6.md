# PPL 0.6 — Real AI Runtime

> Historical note for **0.6**. Current release is **0.10** with a multi-provider registry. Use [REAL_AI_RUNTIME.md](REAL_AI_RUNTIME.md) and [PPL_0.10.md](PPL_0.10.md) for live setup. Env names below (`PPL_OPENAI_*`) still work as aliases; prefer `PPL_AI_PROVIDER` / `PPL_AI_MODEL` / `OPENAI_API_KEY`.

PPL 0.6 moves the language from a mock cognitive runtime toward real model-backed execution while preserving provider neutrality.

## Goals

- real model adapter interface
- OpenAI-compatible HTTP adapter
- environment-based configuration
- schema-validated cognitive outputs
- retry and fallback semantics
- execution telemetry
- offline/local fallback for development

## Runtime architecture

```text
PPL Source
   -> AST
   -> PIR
   -> CognitiveRuntime
        -> AIGateway
             -> ModelAdapter
                  -> OpenAI / Local / (0.10: Anthropic, Google, OpenRouter, …)
```

## Configuration

Set:

```bash
export PPL_AI_PROVIDER=openai
export PPL_OPENAI_API_KEY=...
export PPL_OPENAI_MODEL=gpt-4.1-mini
```

The runtime should choose a provider adapter from configuration. PPL source does not contain provider API calls.

## Cognitive contract

A cognitive operation becomes an `AIRequest` containing:

- operation
- instruction
- input data
- output schema
- allowed classification categories
- model policy

The adapter returns an `AIResponse` containing structured output and execution metadata.

## Validation

The runtime validates output before committing it to application state. Missing fields, invalid types, invalid classifications, and out-of-range confidence are runtime errors.

## Retry and fallback

`MODEL_POLICY` controls retry count and fallback model selection. 0.6 treats fallback as another model identifier; provider-specific routing remains outside the language source.

## Telemetry

Each successful cognitive execution records:

- model
- latency
- input tokens
- output tokens
- cost estimate
- attempts
- validation status

## Security note

API keys must be supplied through environment/secret management and must never be embedded in `.ppl` source or committed to the repository.

## 0.6 non-goals

- provider-specific prompt syntax
- hard-coded model pricing
- production secrets management
- distributed execution
- streaming semantics

Those belong in later releases.
