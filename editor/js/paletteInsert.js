// Resolve where a palette block should be inserted in the program AST.
import { BLOCKS, TOP_LEVEL, WORKFLOW_STEPS, AGENT_BODY, accepts } from "./schema.js";
import { createNode, getNode, getSlot, insertNode, locate } from "./model.js";

function findWorkflowAncestor(program, nodeId) {
  let current = nodeId ? locate(program, nodeId) : null;
  while (current?.node) {
    if (current.node.kind === "workflow") return current.node;
    current = current.parent ? locate(program, current.parent.id) : null;
  }
  return null;
}

function findAgentAncestor(program, nodeId) {
  let current = nodeId ? locate(program, nodeId) : null;
  while (current?.node) {
    if (current.node.kind === "agent") return current.node;
    current = current.parent ? locate(program, current.parent.id) : null;
  }
  return null;
}

/**
 * @returns {{ parent: object, slot: string, index: number } | null}
 */
export function resolvePaletteInsert(program, kind, selectedId) {
  const selected = selectedId ? getNode(program, selectedId) : null;

  if (selected) {
    for (const spec of BLOCKS[selected.kind]?.slots || []) {
      if (accepts(selected, spec.name, kind)) {
        const list = getSlot(selected, spec.name) || [];
        return { parent: selected, slot: spec.name, index: list.length };
      }
    }
  }

  if (WORKFLOW_STEPS.includes(kind)) {
    let wf = findWorkflowAncestor(program, selectedId);
    if (!wf) wf = (program.children || []).find((c) => c.kind === "workflow");
    if (!wf) {
      wf = createNode("workflow");
      insertNode(program, "children", (program.children || []).length, wf);
    }
    const list = getSlot(wf, "children") || [];
    return { parent: wf, slot: "children", index: list.length };
  }

  if (AGENT_BODY.includes(kind)) {
    let agent = selected?.kind === "agent" ? selected : findAgentAncestor(program, selectedId);
    if (!agent) agent = (program.children || []).find((c) => c.kind === "agent");
    if (agent) {
      const list = getSlot(agent, "children") || [];
      return { parent: agent, slot: "children", index: list.length };
    }
  }

  if (TOP_LEVEL.includes(kind) && accepts(program, "children", kind)) {
    return { parent: program, slot: "children", index: (program.children || []).length };
  }

  for (const spec of BLOCKS[selected?.kind]?.slots || []) {
    if (spec.accept.includes(kind)) {
      const list = getSlot(selected, spec.name) || [];
      return { parent: selected, slot: spec.name, index: list.length };
    }
  }

  return null;
}

export function insertPaletteBlock(program, kind, selectedId) {
  const target = resolvePaletteInsert(program, kind, selectedId);
  if (!target) return null;
  const node = createNode(kind);
  insertNode(target.parent, target.slot, target.index, node);
  return node;
}
