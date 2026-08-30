# PPL 0.7 — Production Runtime Plan

PPL 0.7 moves the real-AI runtime toward production execution while preserving the provider-neutral language model established in 0.6.

## Goals

- asynchronous cognitive execution contract
- streaming response contract
- typed provider/runtime error classification
- retry with exponential backoff and jitter hooks
- rate-limit aware execution
- durable execution state abstraction
- execution IDs and resumable state
- model-aware pricing abstraction
- runtime configuration and secret separation
- production-oriented observability

## Runtime architecture

```text
PPL Source
  -> AST
  -> PIR
  -> Runtime
       -> Execution Manager
            -> Retry / Backoff
            -> Rate Limit Handling
            -> Durable State
            -> AI Gateway
                  -> Model Adapter
```

## Provider neutrality

PPL source never contains provider API calls. Provider-specific behavior belongs in adapters.

## Error model

Providers SHOULD map failures into runtime categories:

- `AUTHENTICATION_ERROR`
- `AUTHORIZATION_ERROR`
- `RATE_LIMIT_ERROR`
- `TIMEOUT_ERROR`
- `TRANSIENT_ERROR`
- `VALIDATION_ERROR`
- `PROVIDER_ERROR`
- `NETWORK_ERROR`

The runtime uses these categories to decide whether retry/fallback is appropriate.

## Retry policy

Retries are bounded by `MODEL_POLICY.max_retries`. Exponential backoff SHOULD use jitter. Authentication and validation failures SHOULD NOT be retried automatically.

## Streaming

The adapter contract may expose incremental events:

```text
START
DELTA
DELTA
USAGE
COMPLETE
ERROR
```

PPL source remains unchanged; streaming is a runtime concern.

## Durable execution

Each execution has an ID and state. A durable store SHOULD support:

```text
create(execution)
read(execution_id)
update(execution_id, patch)
append_event(execution_id, event)
```

This allows long-running and resumable workflows.

## Pricing

Model adapters SHOULD expose a pricing descriptor rather than hard-coding pricing into application source. Cost calculation belongs in the runtime telemetry layer.

## Security

Secrets MUST remain outside `.ppl` source. Environment variables, secret managers, or deployment configuration provide credentials.

## Non-goals for 0.7

- distributed scheduler
- production Kubernetes operator
- provider-specific PPL syntax
- persistent vector database implementation
- autonomous learning loops

Those are later platform concerns.
