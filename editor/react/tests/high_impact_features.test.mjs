#!/usr/bin/env node
/**
 * Verifies all 8 high-impact editor UX features are wired up.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { buildFlow } from "../src/astToFlow.js";
import { parsePpl } from "../../js/parse.js";
import { helloWorldDocument } from "../../js/model.js";
import { insertPaletteBlock } from "../../js/paletteInsert.js";
import { validate } from "../../js/validate.js";
import { mapTraceToAstIds } from "../../js/traceMap.js";
import { refLinkedIds, collectRefOptions } from "../../js/refLinks.js";
import { layoutProgram } from "../../js/flow_layout.js";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..", "..");

function read(rel) {
  return readFileSync(join(root, rel), "utf8");
}

// 1. Palette in React Flow editor
assert.ok(read("react/src/Palette.jsx").includes("PALETTE_GROUPS"), "palette sidebar");
assert.ok(read("react/src/App.jsx").includes("<Palette"), "palette mounted in App");

// 2. Blocks view section dividers
assert.ok(read("js/canvas.js").includes("program-section-label"), "blocks view sections");

// 3. Pick-from-list wiring for RUN/RECEIVE
const doc = helloWorldDocument();
assert.ok(collectRefOptions(doc, "run").includes("Classifier"), "agent options");
assert.ok(collectRefOptions(doc, "receive").includes("request"), "input options");
assert.ok(read("react/src/PropertiesPanel.jsx").includes("pick agent"), "react picklist");
assert.ok(read("js/inspector.js").includes("pick agent"), "vanilla picklist");

// 4. Inline rename
assert.ok(read("react/src/nodes.jsx").includes("InlineRename"), "react inline rename");
assert.ok(read("js/flow.js").includes("flow-renamable"), "vanilla inline rename");

// 5. Collapsible APP sections
const collapsed = buildFlow(doc, { collapsed: { declarations: true, workflows: false } });
assert.ok(!collapsed.nodes.some((n) => n.data.kind === "input" || n.data.kind === "agent"), "declarations collapsed hides decl cards");
assert.ok(read("react/src/nodes.jsx").includes("onToggleDecl"), "react collapse toggles");
assert.ok(read("js/flow.js").includes("data-toggle"), "vanilla collapse toggles");

// 6. Validation badges on canvas
const bad = helloWorldDocument();
const runStep = bad.children.find((c) => c.kind === "workflow").children.find((s) => s.kind === "run");
runStep.name = "MissingAgent";
const issues = validate(bad);
assert.ok(issues.some((i) => i.nodeId === runStep.id), "validation attaches nodeId");
const flow = buildFlow(bad, { issuesByNode: new Map([[runStep.id, issues.filter((i) => i.nodeId === runStep.id)]]) });
const badNode = flow.nodes.find((n) => n.data.astId === runStep.id);
assert.equal(badNode?.data.issueLevel, "error", "validation badge data on node");

// 7. Run/trace overlay
const trace = [{ step: "RECEIVE request", type: "D" }, { step: "RUN Classifier", type: "D" }];
const mapped = mapTraceToAstIds(doc, trace);
assert.ok(mapped.executedIds.size >= 2, "trace maps to ast ids");
const traced = buildFlow(doc, { traceState: mapped });
const receiveNode = traced.nodes.find((n) => n.data.kind === "receive");
assert.equal(receiveNode?.data.traceStatus, "executed", "trace highlight on node");

// 8. Hover-linked reference highlighting
const linked = refLinkedIds(doc, runStep.id);
const receive = doc.children.find((c) => c.kind === "workflow").children.find((s) => s.kind === "receive");
const linkedReceive = refLinkedIds(doc, receive.id);
assert.ok(linkedReceive.size >= 2, "receive links to input");
const hoverFlow = buildFlow(doc, { hoverAstId: receive.id, refLinked: linkedReceive });
const inputNode = hoverFlow.nodes.find((n) => n.data.kind === "input");
assert.ok(inputNode?.data.refHighlight, "hover highlights linked declaration");

// Vanilla layout supports same options
const vanilla = layoutProgram(doc, { collapsed: { workflows: true }, issuesByNode: new Map(), traceState: mapped });
assert.ok(vanilla.container.wfCollapsed, "vanilla collapsed workflows");

// Palette insert
const fresh = helloWorldDocument();
const added = insertPaletteBlock(fresh, "tool", null);
assert.ok(added?.kind === "tool", "palette insert creates node");

console.log("high_impact_features OK — all 8 items verified");
