# Running PPL with a Real Model

PPL keeps model configuration outside `.ppl` source. The same application can run against local, OpenAI, OpenRouter, Anthropic, Google, Groq, or Ollama.

## Local development

```bash
ppl check examples/incident.ppl
ppl compile examples/incident.ppl
ppl run examples/incident.ppl
```

Unset `PPL_AI_PROVIDER` (or set `local`) to use the deterministic adapter.

## Provider examples

```bash
# OpenAI (Chat Completions — default live path)
export PPL_AI_PROVIDER=openai
export OPENAI_API_KEY=...
export PPL_AI_MODEL=gpt-4.1-mini

# OpenRouter (route to Claude, Gemini, etc. without native SDKs)
export PPL_AI_PROVIDER=openrouter
export OPENROUTER_API_KEY=...
export PPL_AI_MODEL=anthropic/claude-sonnet-4.5

# Anthropic native
export PPL_AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=...
export PPL_AI_MODEL=claude-sonnet-4-5

# Google Gemini native
export PPL_AI_PROVIDER=google
export GOOGLE_API_KEY=...
export PPL_AI_MODEL=gemini-2.5-flash

# Any OpenAI-compatible host (Azure, Together, vLLM, …)
export PPL_AI_PROVIDER=openai-compatible
export PPL_AI_BASE_URL=https://your-host/v1
export PPL_AI_API_KEY=...
export PPL_AI_MODEL=your-model
```

Never commit API keys.

Optional `ppl.providers.json` in the working directory can set `provider` and `model`; environment variables still win.

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
          +--> retry / same-adapter fallback
          |
          v
      AI Gateway
          |
          v
    Provider registry
      local | openai-compat | anthropic | google | openai-responses
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

A PPL application specifies workload intent and optional `MODEL_POLICY`, not vendor API calls. See [`docs/PPL_0.10.md`](PPL_0.10.md).

## Production checklist

Before connecting a write-capable enterprise tool, verify:

1. schema validation is enabled;
2. retry/fallback limits are bounded;
3. secrets are externalized;
4. execution telemetry is captured;
5. guards and authorization are evaluated;
6. representative evaluations pass;
7. human approval is present for high-risk actions.
