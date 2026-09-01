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


def test_if_fans_out_into_labeled_branches(require_node):
    incident = EDITOR / "templates" / "incident.ppl"
    [item] = _run([incident])
    assert item["edgeKinds"].get("branch", 0) >= 2, "IF should fan out into labeled branches"
    # Every branch in incident's IF ends in RETURN, so the paths terminate and
    # there is no merge point back into the workflow.
    assert item["merges"] == 0, "all-RETURN branches should not merge"


def test_non_terminal_if_merges(require_node, tmp_path):
    source = (
        "APP Demo\n\n"
        "INPUT request\n    text: TEXT\n\n"
        "WORKFLOW Main\n"
        "    RECEIVE request\n"
        "    IF request.text == TRUE\n"
        "        CHECKPOINT a\n"
        "    ELSE\n"
        "        CHECKPOINT b\n"
        "    RETURN request.text\n"
    )
    path = tmp_path / "merge.ppl"
    path.write_text(source, encoding="utf-8")
    [item] = _run([path])
    assert item["merges"] >= 1, "branches that fall through should merge back"
    assert item["edgeKinds"].get("branch", 0) >= 2, "IF should fan out"
