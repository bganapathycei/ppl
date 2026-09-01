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
    assert result["default_input"] == {"request": {"text": "hello there", "done": True}}


def test_run_hello_world():
    result = run_source(HELLO)
    assert result["ok"], result.get("error")
    assert result["result"] == "GREETING"
    assert result["trace"]
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
