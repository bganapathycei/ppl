# Running PPL with a Real Model

PPL keeps model configuration outside `.ppl` source. This lets the same application run against different model providers.

## Local development

The reference runtime can continue to use the local deterministic adapter for language and workflow development.

```bash
ppl check examples/incident.ppl
ppl compile examples/incident.ppl
```

## OpenAI-compatible execution

Configure the environment:

```bash
export PPL_AI_PROVIDER=openai
export PPL_OPENAI_API_KEY="$OPENAI_API_KEY"
export PPL_OPENAI_MODEL="gpt-4.1-mini"
```

Never commit API keys or provider secrets to the repository.

## What happens at runtime

```text
REASON / CLASSIFY / EXTRACT
          |
          v
    AIRequest
          |
          v
    CognitiveRuntime
          |
          +--> retry
          |
          +--> fallback
          |
          v
      AI Gateway
          |
          v
    Model Adapter
          |
          v
    AIResponse
          |
          v
    Schema Validation
          |
          v
     Program State
```

## Provider neutrality

A PPL application should specify workload intent and optional policy, not vendor API calls. The runtime selects the adapter.

A future deployment can therefore use:

```text
OpenAI
Anthropic
Google
Local model
Enterprise gateway
```

without rewriting the PPL program.

## Production checklist

Before connecting a write-capable enterprise tool, verify:

1. schema validation is enabled;
2. retry/fallback limits are bounded;
3. secrets are externalized;
4. execution telemetry is captured;
5. guards and authorization are evaluated;
6. representative evaluations pass;
7. human approval is present for high-risk actions.
