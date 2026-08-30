# PPL 0.10 — Multi-provider LLM runtime

PPL source remains provider-neutral. The runtime selects a model adapter from environment or `ppl.providers.json`. `.ppl` files never contain vendor API calls.

## Providers

| `PPL_AI_PROVIDER` | Transport | Default base |
|---|---|---|
| `local` (default) | Deterministic in-process adapter | n/a |
| `openai` | OpenAI-compatible Chat Completions | `https://api.openai.com/v1` |
| `openrouter` | Chat Completions | `https://openrouter.ai/api/v1` |
| `groq` | Chat Completions | `https://api.groq.com/openai/v1` |
| `ollama` | Chat Completions | `http://127.0.0.1:11434/v1` |
| `openai-compatible` | Chat Completions | `PPL_AI_BASE_URL` required |
| `openai-responses` | OpenAI Responses API | `https://api.openai.com/v1` |
| `anthropic` | Anthropic Messages | `https://api.anthropic.com` |
| `google` / `gemini` | Gemini `generateContent` | Google Generative Language |

Structured outputs are requested per adapter, then **always** re-validated by the PPL schema layer.

## Configuration

Environment (highest precedence):

```bash
export PPL_AI_PROVIDER=openrouter
export PPL_AI_MODEL="anthropic/claude-sonnet-4.5"
export OPENROUTER_API_KEY=...
```

Optional project file `ppl.providers.json`:

```json
{
  "provider": "openrouter",
  "model": "anthropic/claude-sonnet-4.5"
}
```

Do not put API keys in git. Env vars override the file.

`MODEL_POLICY` model slots that are still `reasoning-default` (or other placeholders) are replaced at runtime with `PPL_AI_MODEL` or the provider default. Fallback remains a model id on the **same** adapter. Cross-provider fallback is reserved for 0.10.1.

## Non-goals

- Vendor Python SDKs
- `provider:` syntax in `.ppl` source
- Remote/distributed model routing
- Embedding or image models
