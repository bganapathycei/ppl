#!/usr/bin/env node
import assert from "node:assert/strict";
import { helloWorldDocument, createNode, getSlot } from "../js/model.js";
import { insertPaletteBlock, resolvePaletteInsert } from "../js/paletteInsert.js";
import { WORKFLOW_STEPS, BLOCKS } from "../js/schema.js";

for (const kind of ["print", "let", "read", "write", "for", "while"]) {
  assert.ok(WORKFLOW_STEPS.includes(kind), `${kind} in WORKFLOW_STEPS`);
  assert.ok(BLOCKS[kind], `${kind} in BLOCKS`);
  const node = createNode(kind);
  assert.equal(node.kind, kind, `createNode(${kind})`);
}

const program = helloWorldDocument();
const wf = program.children.find((c) => c.kind === "workflow");
const before = (getSlot(wf, "children") || []).length;

const target = resolvePaletteInsert(program, "print", wf.id);
assert.ok(target, "resolve print insert");
assert.equal(target.parent.kind, "workflow");

const printed = insertPaletteBlock(program, "print", wf.id);
assert.ok(printed?.kind === "print", "insert print");
assert.equal((getSlot(wf, "children") || []).length, before + 1);

const bare = { id: "p", kind: "program", children: [createNode("app"), createNode("workflow", { name: "Main", children: [] })] };
const added = insertPaletteBlock(bare, "print", null);
assert.ok(added?.kind === "print", "insert print into empty workflow");

console.log("palette_insert_print OK");
