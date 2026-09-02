"""Editor /api/run executes programs through the real runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

EDITOR = Path(__file__).resolve().parents[1]
ROOT = EDITOR.parent
sys.path.insert(0, str(EDITOR))
sys.path.insert(0, str(ROOT / "src"))

from serve import compile_source, run_source

HELLO = (EDITOR / "templates" / "hello_world.ppl").read_text(encoding="utf-8")
INCIDENT = (EDITOR / "templates" / "incident.ppl").read_text(encoding="utf-8")
HUMAN_GATE = (EDITOR / "tests" / "fixtures" / "human_gate.ppl").read_text(encoding="utf-8")


def test_compile_includes_default_input():
    result = compile_source(HELLO)
    assert result["ok"]
    # Deterministic hello_world has no INPUT; default_input may be empty.
    assert result["default_input"] in (None, {}, {"request": {"text": "hello there", "done": True}})


def test_run_hello_world():
    result = run_source(HELLO)
    assert result["ok"], result.get("error")
    assert result["result"] == "Hello, world"
    assert result["trace"]
    assert any(item["step"].startswith("LET") or item["step"] == "PRINT" for item in result["trace"])


def test_run_hello_world_ai():
    ai = (EDITOR / "templates" / "hello_world.ppl").read_text(encoding="utf-8")
    # Prefer dedicated AI template when present.
    ai_path = EDITOR / "templates" / "hello_world_ai.ppl"
    if ai_path.exists():
        ai = ai_path.read_text(encoding="utf-8")
    else:
        ai = """APP HelloAI
INPUT request
    text: TEXT
AGENT Classifier
    INPUT request
    CLASSIFY request.text AS
        GREETING
        QUESTION
        OTHER
    OUTPUT
        category
        confidence
WORKFLOW Main
    RECEIVE request
    RUN Classifier
    RETURN Classifier.category
"""
    result = run_source(ai)
    assert result["ok"], result.get("error")
    assert result["result"] in {"GREETING", "QUESTION", "OTHER"}
    assert any(item["step"].startswith("RUN") for item in result["trace"])


def test_run_incident_default_input():
    result = run_source(INCIDENT)
    assert result["ok"], result.get("error")
    assert result["result"] in {"AUTOMATE", "PARTIALLY_AUTOMATE", "KEEP_HUMAN"}


def test_run_human_gate_waits_without_decision():
    result = run_source(HUMAN_GATE)
    assert result["ok"], result.get("error")
    assert result["waiting"] is True
    assert result["wait"]["reason"] == "HUMAN_APPROVAL"
    assert result["execution_id"]


def test_run_human_gate_resumes_with_decision():
    first = run_source(HUMAN_GATE)
    assert first["ok"] and first["waiting"]
    second = run_source(
        HUMAN_GATE,
        execution_id=first["execution_id"],
        human_decision="APPROVE",
    )
    assert second["ok"], second.get("error")
    assert second["result"] == "OK"
    assert not second["waiting"]
