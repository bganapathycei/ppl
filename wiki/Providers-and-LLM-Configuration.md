# Providers and LLM Configuration

PPL source is **provider-neutral**. The runtime selects an adapter from environment or `ppl.providers.json`. `.ppl` files never contain vendor API calls.

## Supported providers

| `PPL_AI_PROVIDER` | Transport | Default base |
|---|---|---|
| `local` (default) | Deterministic in-process | n/a |
| `openai` | OpenAI Chat Completions | `https://api.openai.com/v1` |
| `openrouter` | Chat Completions | `https://openrouter.ai/api/v1` |
| `groq` | Chat Completions | `https://api.groq.com/openai/v1` |
| `ollama` | Chat Completions | `http://127.0.0.1:11434/v1` |
| `openai-compatible` | Chat Completions | `PPL_AI_BASE_URL` required |
| `openai-responses` | OpenAI Responses API | `https://api.openai.com/v1` |
| `anthropic` | Anthropic Messages | `https://api.anthropic.com` |
| `google` / `gemini` | Gemini generateContent | Google Generative Language |

No vendor Python SDKs — HTTP via `urllib` only.

## Quick setup

### OpenAI

```bash
export PPL_AI_PROVIDER=openai
export OPENAI_API_KEY=...
export PPL_AI_MODEL=gpt-4.1-mini
ppl run examples/hello_world.ppl
```

### Anthropic

```bash
export PPL_AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=...
export PPL_AI_MODEL=claude-sonnet-4-5
```

### Google Gemini

```bash
export PPL_AI_PROVIDER=google
export GOOGLE_API_KEY=...
export PPL_AI_MODEL=gemini-2.5-flash
```

### OpenRouter

```bash
export PPL_AI_PROVIDER=openrouter
export OPENROUTER_API_KEY=...
export PPL_AI_MODEL=anthropic/claude-sonnet-4.5
```

### Ollama (local server)

```bash
export PPL_AI_PROVIDER=ollama
export PPL_AI_MODEL=llama3.2
```

### PowerShell

```powershell
$env:PPL_AI_PROVIDER = "openai"
$env:OPENAI_API_KEY = "..."
$env:PPL_AI_MODEL = "gpt-4.1-mini"
```

## Configuration file

Optional `ppl.providers.json` (do not commit API keys):

```json
{
  "provider": "openrouter",
  "model": "anthropic/claude-sonnet-4.5"
}
```

Environment variables **override** the file. Override file path: `PPL_PROVIDERS_FILE`.

## API key env vars

| Provider | Key variables |
|---|---|
| OpenAI | `OPENAI_API_KEY`, `PPL_OPENAI_API_KEY`, `PPL_AI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY`, `PPL_AI_API_KEY` |
| Google | `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `PPL_AI_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY`, `PPL_AI_API_KEY` |
| Groq | `GROQ_API_KEY`, `PPL_AI_API_KEY` |

## MODEL_POLICY

```text
MODEL_POLICY EnterpriseDefault
    reasoning: reasoning-default
    classification: classification-default
    max_retries: 2
    fallback: fallback-default
```

Placeholder slots like `reasoning-default` are replaced at runtime with `PPL_AI_MODEL` or the provider default. Fallback is a model on the **same** adapter. Cross-provider fallback is planned for 0.10.1.

## Structured output

Adapters request JSON per provider capabilities. PPL **always re-validates** against the declared schema before committing to program state.

## Local development

Unset `PPL_AI_PROVIDER` (or set `local`) for offline deterministic runs. No API key required.

## Visual editor AI assistant

The browser editor (`python editor/serve.py`) exposes an **AI Assistant** panel with the same provider registry. Chat requires a live adapter; program **Run** in the editor still works with `local`.

1. Set env vars (see Quick setup above).
2. Start `python editor/serve.py`.
3. Pick provider and model in the assistant sidebar.
4. Describe edits in natural language; **Apply to editor** when PPL validates.

`GET /api/assistant/config` lists providers and key availability. `POST /api/assistant/chat` sends messages plus optional `current_source`.

See [[Visual Editor]].

## Production checklist

Before write-capable tools in production:

1. Schema validation enabled
2. Retry/fallback limits bounded
3. Secrets externalized (never in `.ppl` or git)
4. Execution telemetry captured
5. Guards and authorization evaluated
6. Representative evaluations pass
7. Human approval for high-risk actions

---

**See also:** [[Visual Editor]] · [[Architecture]] · [[Examples]]
