from ppl.ai_gateway import AIRequest, ModelPolicy
from ppl.production_runtime import PPLRuntimeError, RuntimeErrorCode
from ppl.provider import SUPPORTED, build_adapter
from ppl.providers.anthropic import AnthropicAdapter
from ppl.providers.google import GoogleAdapter
from ppl.providers.openai_compatible import OpenAICompatibleAdapter
from ppl.providers.structured import json_schema_for_request, parse_json_object, resolve_model


def _request(**kwargs) -> AIRequest:
    policy = kwargs.pop("policy", ModelPolicy(reasoning_model="reasoning-default"))
    return AIRequest(
        operation=kwargs.get("operation", "REASON"),
        instruction=kwargs.get("instruction", "determine whether this incident is repetitive"),
        input_data=kwargs.get("input_data", {"description": "Repeated outage"}),
        schema=kwargs.get("schema", {"repetitive": "BOOLEAN", "confidence": "CONFIDENCE"}),
        categories=kwargs.get("categories", []),
        policy=policy,
    )


def test_chat_completions_parses_json(monkeypatch):
    captured = {}

    def fake_post(url, payload, headers, timeout=60.0):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        return {
            "model": "gpt-4.1-mini",
            "choices": [{"message": {"content": '{"repetitive": true, "confidence": 0.9}'}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

    monkeypatch.setattr("ppl.providers.openai_compatible.post_json", fake_post)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    adapter = OpenAICompatibleAdapter(alias="openai")
    response = adapter.execute(_request())
    assert "/chat/completions" in captured["url"]
    assert captured["payload"]["response_format"] == {"type": "json_object"}
    assert response.output["repetitive"] is True
    assert response.input_tokens == 10


def test_openrouter_alias_sets_base_url(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
    adapter = OpenAICompatibleAdapter(alias="openrouter")
    assert adapter.base_url == "https://openrouter.ai/api/v1"
    captured = {}

    def fake_post(url, payload, headers, timeout=60.0):
        captured["url"] = url
        captured["headers"] = headers
        return {"choices": [{"message": {"content": '{"repetitive": false, "confidence": 0.5}'}}]}

    monkeypatch.setattr("ppl.providers.openai_compatible.post_json", fake_post)
    adapter.execute(_request())
    assert captured["url"].startswith("https://openrouter.ai/api/v1/chat/completions")
    assert captured["headers"].get("HTTP-Referer")


def test_anthropic_builds_messages_payload(monkeypatch):
    captured = {}

    def fake_post(url, payload, headers, timeout=60.0):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        return {
            "model": "claude-sonnet-4-5",
            "content": [{"type": "text", "text": '{"repetitive": true, "confidence": 0.8}'}],
            "usage": {"input_tokens": 3, "output_tokens": 4},
        }

    monkeypatch.setattr("ppl.providers.anthropic.post_json", fake_post)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-test")
    adapter = AnthropicAdapter()
    response = adapter.execute(_request())
    assert captured["url"].endswith("/v1/messages")
    assert captured["headers"]["x-api-key"] == "ant-test"
    assert captured["payload"]["messages"][0]["role"] == "user"
    assert "JSON Schema" in captured["payload"]["messages"][0]["content"]
    assert response.output["confidence"] == 0.8


def test_google_attaches_response_mime_type(monkeypatch):
    captured = {}

    def fake_post(url, payload, headers, timeout=60.0):
        captured["url"] = url
        captured["payload"] = payload
        return {
            "candidates": [{"content": {"parts": [{"text": '{"repetitive": true, "confidence": 0.7}'}]}}],
            "usageMetadata": {"promptTokenCount": 2, "candidatesTokenCount": 3},
        }

    monkeypatch.setattr("ppl.providers.google.post_json", fake_post)
    monkeypatch.setenv("GOOGLE_API_KEY", "g-test")
    adapter = GoogleAdapter()
    adapter.execute(_request())
    assert "generateContent" in captured["url"]
    gen = captured["payload"]["generationConfig"]
    assert gen["responseMimeType"] == "application/json"
    assert gen["responseSchema"]["type"] == "object"


def test_build_adapter_rejects_unknown(monkeypatch, tmp_path):
    monkeypatch.setenv("PPL_AI_PROVIDER", "not-a-vendor")
    monkeypatch.setenv("PPL_PROVIDERS_FILE", str(tmp_path / "missing.json"))
    try:
        build_adapter()
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Unsupported PPL_AI_PROVIDER" in str(exc)
        for name in ("openai", "openrouter", "anthropic", "google"):
            assert name in str(exc)
        assert "local" in str(exc)
    for name in SUPPORTED:
        assert name


def test_build_adapter_local_default(monkeypatch, tmp_path):
    monkeypatch.delenv("PPL_AI_PROVIDER", raising=False)
    monkeypatch.setenv("PPL_PROVIDERS_FILE", str(tmp_path / "missing.json"))
    adapter = build_adapter()
    from ppl.ai_gateway import LocalModelAdapter
    assert isinstance(adapter, LocalModelAdapter)


def test_providers_json_file(monkeypatch, tmp_path):
    cfg = tmp_path / "ppl.providers.json"
    cfg.write_text('{"provider":"openrouter","model":"anthropic/claude-sonnet-4.5"}', encoding="utf-8")
    monkeypatch.delenv("PPL_AI_PROVIDER", raising=False)
    monkeypatch.setenv("PPL_PROVIDERS_FILE", str(cfg))
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-file")
    adapter = build_adapter()
    assert isinstance(adapter, OpenAICompatibleAdapter)
    assert adapter.alias == "openrouter"
    assert adapter.default_model == "anthropic/claude-sonnet-4.5"


def test_resolve_model_substitutes_placeholder(monkeypatch):
    monkeypatch.setenv("PPL_AI_MODEL", "openai/gpt-4.1-mini")
    model = resolve_model(_request(), "fallback-default")
    assert model == "openai/gpt-4.1-mini"


def test_parse_json_object_from_fenced_block():
    parsed = parse_json_object('```json\n{"a": 1}\n```')
    assert parsed == {"a": 1}


def test_http_status_mapping():
    from ppl.providers.http import map_http_status
    err = map_http_status(429, "slow down")
    assert isinstance(err, PPLRuntimeError)
    assert err.code is RuntimeErrorCode.RATE_LIMIT_ERROR
    assert err.retryable


def test_json_schema_for_classify():
    req = _request(
        operation="CLASSIFY",
        schema={"category": "CLASSIFICATION", "confidence": "CONFIDENCE"},
        categories=["ACCESS", "DATABASE"],
    )
    schema = json_schema_for_request(req)
    assert schema["properties"]["category"]["enum"] == ["ACCESS", "DATABASE"]
