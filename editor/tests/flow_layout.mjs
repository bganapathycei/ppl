#!/usr/bin/env node
/**
 * Exercise the flow canvas auto-layout on bundled .ppl sources and emit JSON
 * for pytest to assert on. Verifies geometry is finite, every selectable node
 * maps to a real AST id, and branching constructs (IF/PARALLEL) fan out and
 * merge.
 *
 * Usage: node editor/tests/flow_layout.mjs [file.ppl ...]
 */

import { readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { parsePpl } from "../js/parse.js";
import { layoutProgram } from "../js/flow_layout.js";
import { walk } from "../js/model.js";

const here = dirname(fileURLToPath(import.meta.url));
const templatesDir = join(here, "..", "templates");

function collectIds(doc) {
  const ids = new Set();
  walk(doc, (node) => ids.add(node.id));
  return ids;
}

function finite(n) {
  return typeof n === "number" && Number.isFinite(n);
}

function analyze(path) {
  const doc = parsePpl(readFileSync(path, "utf8"));
  const layout = layoutProgram(doc, { maxWidth: 1100 });
  const ids = collectIds(doc);

  let geometryOk = finite(layout.width) && finite(layout.height) && layout.width > 0 && layout.height > 0;
  let danglingSelectable = 0;
  const selectable = [];
  for (const item of layout.items) {
    if (!finite(item.x) || !finite(item.y) || !finite(item.w) || !finite(item.h)) geometryOk = false;
    if (item.selectable) {
      selectable.push(item.nodeKind);
      if (!ids.has(item.id)) danglingSelectable += 1;
    }
  }
  for (const edge of layout.edges) {
    if (![edge.x1, edge.y1, edge.x2, edge.y2].every(finite)) geometryOk = false;
  }

  const edgeKinds = {};
  for (const edge of layout.edges) edgeKinds[edge.kind] = (edgeKinds[edge.kind] || 0) + 1;

  return {
    file: path,
    ok: geometryOk && danglingSelectable === 0,
    geometryOk,
    danglingSelectable,
    width: layout.width,
    height: layout.height,
    itemCount: layout.items.length,
    selectableCount: selectable.length,
    merges: layout.items.filter((i) => i.kind === "merge").length,
    addChips: layout.items.filter((i) => i.kind === "add").length,
    edgeKinds,
  };
}

function collectPaths(argv) {
  if (argv.length) return argv.map((item) => resolve(item));
  return readdirSync(templatesDir)
    .filter((name) => name.endsWith(".ppl"))
    .map((name) => join(templatesDir, name))
    .sort();
}

const results = collectPaths(process.argv.slice(2)).map(analyze);
const failed = results.filter((item) => !item.ok);
process.stdout.write(JSON.stringify({ results, failed: failed.length }));
process.exit(failed.length ? 1 : 0);
