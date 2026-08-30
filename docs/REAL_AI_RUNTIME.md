# Running PPL with a real model

PPL keeps model configuration outside `.ppl` source. The same application can run against local, OpenAI, OpenRouter, Anthropic, Google, Groq, or Ollama.

**Do this first:** complete [GETTING_STARTED.md](GETTING_STARTED.md) through the first `ppl run` on `examples/hello_world.ppl` with the default `local` adapter (no API key). Come back here only when you want a live model. Adapter details: [PPL_0.10.md](PPL_0.10.md).

## 1. Confirm local development still works

```bash
ppl check examples/incident.ppl
ppl compile examples/incident.ppl
ppl run examples/incident.ppl
```

Unset `PPL_AI_PROVIDER` (or set `local`) to use the deterministic adapter. No API key is required. If this fails, stop and fix install/PATH using Getting Started Steps 3–5 before configuring a provider.

## 2. Choose a provider and set env vars (do not edit `.ppl` files)

bash:

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

# Groq
export PPL_AI_PROVIDER=groq
export GROQ_API_KEY=...

# Ollama (local server; API key optional)
export PPL_AI_PROVIDER=ollama
export PPL_AI_MODEL=llama3.2

# Any OpenAI-compatible host (Azure, Together, vLLM, …)
export PPL_AI_PROVIDER=openai-compatible
export PPL_AI_BASE_URL=https://your-host/v1
export PPL_AI_API_KEY=...
export PPL_AI_MODEL=your-model

ppl run examples/hello_world.ppl
```

PowerShell:

```powershell
$env:PPL_AI_PROVIDER = "openai"
$env:OPENAI_API_KEY = "..."
$env:PPL_AI_MODEL = "gpt-4.1-mini"
ppl run examples/hello_world.ppl
```

Never commit API keys. If a run fails with an auth error, unset `PPL_AI_PROVIDER` to return to `local`.

Optional `ppl.providers.json` in the working directory can set `provider` and `model`; environment variables still win. Do not put `api_key` in a file that is committed.

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
