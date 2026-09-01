"""AI coding assistant for the PPL visual editor (natural language -> .ppl)."""

from __future__ import annotations

import os
import re
from typing import Any

from ppl.parser import parse
from ppl.providers.openai_compatible import PRESETS, OpenAICompatibleAdapter, _first_env
from ppl.providers.http import post_json

SYSTEM_PROMPT = """You are the PPL coding assistant embedded in the PPL visual editor.
PPL (Prompt Programming Language) 0.10 is an AI-native language for agents, workflows, governance, and tools.

Help users create, edit, and maintain complete PPL programs using natural language.
When you propose or change a program, include the FULL updated program in a fenced code block:

```ppl
APP Example
...
```

Rules:
- Emit valid PPL 0.10 syntax only inside ```ppl blocks.
- Top-level declarations: APP, INPUT, MODEL_POLICY, KNOWLEDGE, MEMORY, TOOL, GUARD, AUTHORIZATION, BUDGET, ENVIRONMENT, AGENT, WORKFLOW.
- Agent ops: CLASSIFY, EXTRACT, REASON, OUTPUT. Workflow: RECEIVE, RUN, IF, RETURN, HUMAN_APPROVAL, PARALLEL, JOIN, WAIT, CHECKPOINT, CALL.
- Use indentation (4 spaces) for nested clauses. Never embed vendor API names in source.
- Explain changes briefly outside the code block. Ask clarifying questions when requirements are ambiguous.
- If the user only asks a question, answer without a ```ppl block unless they want edits.
"""

MODEL_CATALOG: dict[str, dict[str, Any]] = {
    "openai": {
        "label": "OpenAI",
        "models": [
            {"id": "gpt-4.1-mini", "label": "GPT-4.1 Mini"},
            {"id": "gpt-4.1", "label": "GPT-4.1"},
            {"id": "gpt-4o-mini", "label": "GPT-4o Mini"},
            {"id": "gpt-4o", "label": "GPT-4o"},
        ],
        "key_envs": PRESETS["openai"]["key_envs"],
    },
    "openrouter": {
        "label": "OpenRouter",
        "models": [
            {"id": "openai/gpt-4.1-mini", "label": "OpenAI GPT-4.1 Mini"},
            {"id": "anthropic/claude-sonnet-4.5", "label": "Claude Sonnet 4.5"},
            {"id": "google/gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
            {"id": "meta-llama/llama-3.3-70b-instruct", "label": "Llama 3.3 70B"},
        ],
        "key_envs": PRESETS["openrouter"]["key_envs"],
    },
    "anthropic": {
        "label": "Anthropic",
        "models": [
            {"id": "claude-sonnet-4-5", "label": "Claude Sonnet 4.5"},
            {"id": "claude-3-5-haiku-latest", "label": "Claude 3.5 Haiku"},
        ],
        "key_envs": "PPL_AI_API_KEY,ANTHROPIC_API_KEY",
    },
    "google": {
        "label": "Google Gemini",
        "models": [
            {"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
            {"id": "gemini-2.0-flash", "label": "Gemini 2.0 Flash"},
        ],
        "key_envs": "PPL_AI_API_KEY,GOOGLE_API_KEY,GEMINI_API_KEY",
    },
    "groq": {
        "label": "Groq",
        "models": [
            {"id": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B"},
            {"id": "llama-3.1-8b-instant", "label": "Llama 3.1 8B"},
        ],
        "key_envs": PRESETS["groq"]["key_envs"],
    },
    "ollama": {
        "label": "Ollama (local)",
        "models": [
            {"id": "llama3.2", "label": "Llama 3.2"},
            {"id": "mistral", "label": "Mistral"},
            {"id": "qwen2.5", "label": "Qwen 2.5"},
        ],
        "key_envs": PRESETS["ollama"]["key_envs"],
        "optional_key": True,
    },
    "openai-compatible": {
        "label": "OpenAI-compatible",
        "models": [{"id": "gpt-4.1-mini", "label": "Custom model"}],
        "key_envs": PRESETS["openai-compatible"]["key_envs"],
        "needs_base_url": True,
    },
}


def _provider_ready(provider_id: str) -> bool:
    meta = MODEL_CATALOG.get(provider_id)
    if not meta:
        return False
    if meta.get("optional_key"):
        return True
    return bool(_first_env(str(meta["key_envs"])))


def _default_provider() -> str:
    env = (os.getenv("PPL_AI_PROVIDER") or "openai").strip().lower()
    if env in {"local", "mock", ""}:
        for candidate in ("openai", "openrouter", "anthropic", "google", "groq", "ollama"):
            if _provider_ready(candidate):
                return candidate
        return "openai"
    if env == "gemini":
        return "google"
    return env if env in MODEL_CATALOG else "openai"


def assistant_config() -> dict:
    providers = []
    default_provider = _default_provider()
    for provider_id, meta in MODEL_CATALOG.items():
        default_model = meta["models"][0]["id"]
        if provider_id == default_provider:
            default_model = os.getenv("PPL_AI_MODEL") or default_model
        providers.append(
            {
                "id": provider_id,
                "label": meta["label"],
                "models": meta["models"],
                "configured": _provider_ready(provider_id),
                "needs_base_url": bool(meta.get("needs_base_url")),
                "default_model": default_model,
            }
        )
    return {
        "ok": True,
        "providers": providers,
        "default_provider": default_provider,
        "default_model": os.getenv("PPL_AI_MODEL") or MODEL_CATALOG[default_provider]["models"][0]["id"],
    }


def extract_ppl(text: str) -> str | None:
    if not text:
        return None
    for pattern in (r"```ppl\s*\n(.*?)```", r"```\s*\n(APP[\s\S]*?)```"):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            body = match.group(1).strip()
            if body.startswith("APP"):
                return body + ("\n" if not body.endswith("\n") else "")
    return None


def validate_ppl(source: str | None) -> tuple[bool, str | None]:
    if not source:
        return False, None
    try:
        parse(source)
        return True, None
    except Exception as exc:
        return False, f"{exc.__class__.__name__}: {exc}"


def _chat_openai_compatible(provider: str, model: str, messages: list[dict], system: str) -> str:
    adapter = OpenAICompatibleAdapter(alias=provider, default_model=model)
    payload = {
        "model": model or adapter.default_model,
        "messages": [{"role": "system", "content": system}, *messages],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {adapter.api_key or 'ollama'}"}
    if provider == "openrouter":
        headers.setdefault("HTTP-Referer", os.getenv("PPL_OPENROUTER_REFERER", "https://github.com/bganapathycei/ppl"))
        headers.setdefault("X-Title", os.getenv("PPL_OPENROUTER_TITLE", "PPL Editor"))
    parsed = post_json(f"{adapter.base_url}/chat/completions", payload, headers, timeout=120.0)
    return parsed["choices"][0]["message"]["content"]


def _chat_anthropic(model: str, messages: list[dict], system: str) -> str:
    api_key = _first_env("PPL_AI_API_KEY,ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Anthropic API key not configured")
    base_url = (os.getenv("PPL_AI_BASE_URL") or "https://api.anthropic.com").rstrip("/")
    payload = {
        "model": model or os.getenv("PPL_AI_MODEL") or "claude-sonnet-4-5",
        "max_tokens": int(os.getenv("PPL_AI_MAX_TOKENS", "4096")),
        "system": system,
        "messages": messages,
    }
    parsed = post_json(
        f"{base_url}/v1/messages",
        payload,
        {"x-api-key": api_key, "anthropic-version": os.getenv("PPL_ANTHROPIC_VERSION", "2023-06-01")},
        timeout=120.0,
    )
    for block in parsed.get("content") or []:
        if block.get("type") == "text":
            return block["text"]
    raise RuntimeError("Anthropic response missing text")


def _chat_google(model: str, messages: list[dict], system: str) -> str:
    api_key = _first_env("PPL_AI_API_KEY,GOOGLE_API_KEY,GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Google API key not configured")
    base_url = (os.getenv("PPL_AI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    chosen = model or os.getenv("PPL_AI_MODEL") or "gemini-2.5-flash"
    contents = []
    for item in messages:
        role = "user" if item["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": item["content"]}]})
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.2},
    }
    parsed = post_json(f"{base_url}/models/{chosen}:generateContent?key={api_key}", payload, {}, timeout=120.0)
    parts = parsed["candidates"][0]["content"]["parts"]
    return "".join(p["text"] for p in parts if isinstance(p.get("text"), str))


def assistant_chat(
    messages: list[dict[str, str]],
    *,
    provider: str,
    model: str,
    current_source: str = "",
) -> dict:
    provider = (provider or _default_provider()).strip().lower()
    if provider in {"local", "mock"}:
        return {
            "ok": False,
            "error": "Configure a live provider (OpenAI, OpenRouter, Anthropic, Google, Groq, or Ollama) for the coding assistant.",
        }
    if provider not in MODEL_CATALOG:
        return {"ok": False, "error": f"Unknown provider: {provider}"}
    if not _provider_ready(provider) and not MODEL_CATALOG[provider].get("optional_key"):
        meta = MODEL_CATALOG[provider]
        return {
            "ok": False,
            "error": f"{meta['label']} API key not configured. Set one of: {meta['key_envs']}",
        }

    system = SYSTEM_PROMPT
    if current_source.strip():
        system += f"\n\nCurrent editor program:\n```ppl\n{current_source.strip()}\n```"

    normalized = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
        if m.get("role") in {"user", "assistant"} and isinstance(m.get("content"), str)
    ]
    if not normalized or normalized[-1]["role"] != "user":
        return {"ok": False, "error": "Last message must be from the user"}

    try:
        if provider in {"openai", "openrouter", "groq", "ollama", "openai-compatible"}:
            reply = _chat_openai_compatible(provider, model, normalized, system)
        elif provider == "anthropic":
            reply = _chat_anthropic(model, normalized, system)
        elif provider in {"google", "gemini"}:
            reply = _chat_google(model, normalized, system)
        else:
            return {"ok": False, "error": f"Unsupported provider: {provider}"}
    except Exception as exc:
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}

    ppl_source = extract_ppl(reply)
    valid, parse_error = validate_ppl(ppl_source)
    return {
        "ok": True,
        "reply": reply,
        "provider": provider,
        "model": model,
        "ppl_source": ppl_source,
        "ppl_valid": valid,
        "ppl_error": parse_error,
        "error": None,
    }
