"""Validate the flow canvas auto-layout (editor/js/flow_layout.js) via Node."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

EDITOR = Path(__file__).resolve().parents[1]
LAYOUT = EDITOR / "tests" / "flow_layout.mjs"


@pytest.fixture(scope="module")
def require_node():
    if shutil.which("node") is None:
        pytest.skip("node is required for flow layout tests")
    proc = subprocess.run(["node", "--version"], capture_output=True, text=True)
    if proc.returncode != 0:
        pytest.skip(f"node unavailable: {proc.stderr.strip()}")


def _run(extra_paths: list[Path] | None = None) -> list[dict]:
    cmd = ["node", str(LAYOUT)]
    if extra_paths:
        cmd.extend(str(path) for path in extra_paths)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=EDITOR)
    if proc.returncode != 0 and not proc.stdout.strip():
        raise AssertionError(f"flow_layout.mjs failed:\n{proc.stderr}")
    return json.loads(proc.stdout)["results"]


def test_layout_geometry_and_ids(require_node):
    results = _run()
    assert len(results) >= 4, "expected bundled templates"
    for item in results:
        assert item["geometryOk"], f"{item['file']}: non-finite geometry"
        assert item["danglingSelectable"] == 0, f"{item['file']}: selectable node without AST id"
        assert item["selectableCount"] > 0, f"{item['file']}: nothing selectable"
        assert item["addChips"] >= 1, f"{item['file']}: missing add affordance"


def test_branching_examples_fan_out_and_merge(require_node):
    incident = EDITOR / "templates" / "incident.ppl"
    [item] = _run([incident])
    assert item["merges"] >= 1, "IF should produce a merge point"
    assert item["edgeKinds"].get("branch", 0) >= 2, "IF should fan out into labeled branches"
