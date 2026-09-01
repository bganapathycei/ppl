"""Round-trip editor-style .ppl through the real parser and compiler."""

from __future__ import annotations

import sys
from pathlib import Path

EDITOR = Path(__file__).resolve().parents[1]
ROOT = EDITOR.parent
sys.path.insert(0, str(EDITOR))
sys.path.insert(0, str(ROOT / "src"))

from ppl.compiler import Compiler
from ppl.parser import parse

from serve import compile_source

CODEGEN_HELLO = """APP HelloAI

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

CODEGEN_IF = """APP Branchy

INPUT request
    text: TEXT

AGENT Classifier
    INPUT request
    CLASSIFY request.text AS
        GREETING
        OTHER
    OUTPUT
        category
        confidence

WORKFLOW Main
    RECEIVE request
    RUN Classifier
    IF Classifier.confidence < 0.90
        HUMAN_APPROVAL
            QUESTION:
                validate before continuing
            OPTIONS:
                APPROVE
                REJECT
    ELSE IF Classifier.confidence == 1
        RETURN "SURE"
    ELSE
        RETURN "NO"
    RETURN Classifier.category
"""


def test_editor_codegen_style_hello_world():
    first = Compiler().compile(parse(CODEGEN_HELLO))
    again = compile_source(CODEGEN_HELLO)
    assert again["ok"]
    assert first["application"] == "HelloAI"
    assert [n["operation"] for n in first["graph"]["nodes"]] == ["RECEIVE", "RUN", "RETURN"]


def test_editor_codegen_style_if_else():
    result = compile_source(CODEGEN_IF)
    assert result["ok"], result["error"]
    ops = [node["operation"] for node in result["graph"]["nodes"]]
    assert "IF" in ops
    assert "HUMAN_APPROVAL" in ops
    assert "RETURN" in ops
    assert "JOIN" in ops
