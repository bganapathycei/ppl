"""Round-trip bundled .ppl through editor parse.js/codegen.js, then ppl.Compiler."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

EDITOR = Path(__file__).resolve().parents[1]
ROOT = EDITOR.parent
sys.path.insert(0, str(EDITOR))
sys.path.insert(0, str(ROOT / "src"))

from serve import compile_source

ROUNDTRIP = EDITOR / "tests" / "roundtrip.mjs"


@pytest.fixture(scope="module")
def require_node():
    if shutil.which("node") is None:
        pytest.skip("node is required for editor JS round-trip tests")
    proc = subprocess.run(["node", "--version"], capture_output=True, text=True)
    if proc.returncode != 0:
        pytest.skip(f"node unavailable: {proc.stderr.strip()}")


def _run_roundtrip(extra_paths: list[Path] | None = None) -> list[dict]:
    cmd = ["node", str(ROUNDTRIP)]
    if extra_paths:
        cmd.extend(str(path) for path in extra_paths)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=EDITOR)
    if proc.returncode != 0 and not proc.stdout.strip():
        raise AssertionError(f"roundtrip.mjs failed:\n{proc.stderr}")
    payload = json.loads(proc.stdout)
    if payload.get("failed"):
        lines = []
        for item in payload["results"]:
            if not item.get("ok"):
                lines.append(f"{item['file']}: {item.get('error')}")
        raise AssertionError("JS round-trip failed:\n" + "\n".join(lines))
    return payload["results"]


def test_js_roundtrip_all_editor_sources(require_node):
    results = _run_roundtrip()
    assert len(results) >= 6, "expected templates, fixtures, and snapshots"
    for item in results:
        compiled = compile_source(item["source"])
        assert compiled["ok"], f"{item['file']}: {compiled['error']}"
        assert compiled["application"] == item["application"]
        assert item.get("stable"), f"{item['file']}: codegen not stable on re-parse"


def test_js_roundtrip_each_template(require_node):
    templates = sorted((EDITOR / "templates").glob("*.ppl"))
    assert templates
    for path in templates:
        item = _run_roundtrip([path])[0]
        compiled = compile_source(item["source"])
        assert compiled["ok"], f"{path.name}: {compiled['error']}"
        assert compiled["graph"]["nodes"], f"{path.name}: empty graph"
