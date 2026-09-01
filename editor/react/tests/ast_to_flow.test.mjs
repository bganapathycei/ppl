#!/usr/bin/env node
// Minimal assertions for the React Flow graph builder. Run with `npm test`
// (requires installed dependencies for @dagrejs/dagre).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { buildFlow } from "../src/astToFlow.js";
import { parsePpl } from "../../js/parse.js";
import { walk } from "../../js/model.js";

const here = dirname(fileURLToPath(import.meta.url));
const templates = join(here, "..", "..", "templates");

function load(name) {
  return parsePpl(readFileSync(join(templates, `${name}.ppl`), "utf8"));
}

function check(name) {
  const doc = load(name);
  const ids = new Set();
  walk(doc, (n) => ids.add(n.id));
  const { nodes, edges } = buildFlow(doc);

  assert.ok(nodes.length > 0, `${name}: no nodes`);
  const nodeIds = new Set(nodes.map((n) => n.id));
  for (const edge of edges) {
    assert.ok(nodeIds.has(edge.source), `${name}: edge source ${edge.source} missing`);
    assert.ok(nodeIds.has(edge.target), `${name}: edge target ${edge.target} missing`);
  }
  for (const node of nodes) {
    assert.ok(Number.isFinite(node.position.x) && Number.isFinite(node.position.y), `${name}: bad position`);
    if (node.data.astId) assert.ok(ids.has(node.data.astId), `${name}: dangling astId ${node.data.astId}`);
  }
  // RETURN nodes terminate: no outgoing edge.
  for (const node of nodes) {
    if (node.data.kind === "return") {
      const out = edges.filter((e) => e.source === node.id);
      assert.equal(out.length, 0, `${name}: RETURN ${node.id} should not have an outgoing edge`);
    }
  }
  return { name, nodes: nodes.length, edges: edges.length };
}

const summary = ["hello_world", "incident", "governed_change", "enterprise_automation"].map(check);

// incident's IF must fan out into labeled branches.
const incident = buildFlow(load("incident"));
const branchEdges = incident.edges.filter((e) => e.data?.kind === "branch");
assert.ok(branchEdges.length >= 2, "incident: IF should fan out into labeled branches");
assert.ok(branchEdges.every((e) => e.label), "incident: branch edges should be labeled");

console.log("ast_to_flow OK", JSON.stringify(summary));
