"""AI coding assistant helpers and config."""

from __future__ import annotations

import sys
from pathlib import Path

EDITOR = Path(__file__).resolve().parents[1]
ROOT = EDITOR.parent
sys.path.insert(0, str(EDITOR))
sys.path.insert(0, str(ROOT / "src"))

from assistant import assistant_config, extract_ppl, validate_ppl

HELLO = (EDITOR / "templates" / "hello_world.ppl").read_text(encoding="utf-8")


def test_extract_ppl_from_fence():
    reply = "Here is the program:\n```ppl\nAPP Demo\n\nINPUT request\n    text: TEXT\n```\n"
    body = extract_ppl(reply)
    assert body is not None
    assert body.startswith("APP Demo")


def test_extract_ppl_generic_fence_with_app():
    reply = "```\nAPP Fallback\n\nWORKFLOW Main\n    RETURN \"OK\"\n```"
    body = extract_ppl(reply)
    assert body is not None
    assert "APP Fallback" in body


def test_extract_ppl_missing():
    assert extract_ppl("No code here") is None


def test_validate_ppl_ok():
    ok, err = validate_ppl(HELLO)
    assert ok
    assert err is None


def test_validate_ppl_bad():
    ok, err = validate_ppl("APP Broken\n    SYNTAX ???")
    assert not ok
    assert err


def test_assistant_config_shape():
    cfg = assistant_config()
    assert cfg["ok"] is True
    assert cfg["providers"]
    ids = {item["id"] for item in cfg["providers"]}
    assert "openai" in ids
    assert "openrouter" in ids
    for provider in cfg["providers"]:
        assert provider["label"]
        assert provider["models"]
        assert "configured" in provider
