"""Editor templates and codegen snapshots must parse with the real PPL compiler."""

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

TEMPLATES = EDITOR / "templates"
SNAPSHOTS = Path(__file__).resolve().parent / "snapshots"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _compile(path: Path):
    return Compiler().compile(parse(path.read_text(encoding="utf-8")))


def test_templates_compile():
    paths = sorted(TEMPLATES.glob("*.ppl"))
    assert paths, "expected editor templates"
    for path in paths:
        pir = _compile(path)
        assert pir["application"]
        assert pir["graph"]["nodes"]


def test_codegen_hello_world_snapshot_compiles():
    pir = _compile(SNAPSHOTS / "hello_world_codegen.ppl")
    assert pir["application"] == "HelloAI"
    ops = [node["operation"] for node in pir["graph"]["nodes"]]
    assert ops == ["RECEIVE", "RUN", "RETURN"]


def test_complete_constructs_compile():
    pir = _compile(FIXTURES / "complete.ppl")
    assert pir["application"] == "CompleteEditor"
    ops = {node["operation"] for node in pir["graph"]["nodes"]}
    for needed in {"RECEIVE", "RUN", "JOIN", "WAIT", "CHECKPOINT", "CALL", "IF", "HUMAN_APPROVAL", "RETURN"}:
        assert needed in ops


def test_compile_source_api_accepts_templates():
    source = (TEMPLATES / "incident.ppl").read_text(encoding="utf-8")
    result = compile_source(source)
    assert result["ok"] is True
    assert result["application"] == "IncidentAdvisor"
    assert result["graph"]["nodes"]


def test_compile_source_api_rejects_empty():
    result = compile_source("")
    assert result["ok"] is False
    assert result["error"]


def test_all_template_sources_via_compile_api():
    for path in sorted(TEMPLATES.glob("*.ppl")):
        result = compile_source(path.read_text(encoding="utf-8"))
        assert result["ok"], f"{path.name}: {result['error']}"
