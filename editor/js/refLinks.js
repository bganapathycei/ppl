import { getNode } from "./model.js";

/** IDs linked by RECEIVE/RUN reference wiring for hover highlighting. */
export function refLinkedIds(program, astId) {
  if (!astId) return new Set();
  const node = getNode(program, astId);
  if (!node) return new Set();
  const children = program.children || [];
  const linked = new Set([astId]);
  if (node.kind === "receive") {
    const input = children.find((c) => c.kind === "input" && c.name === node.name);
    if (input) linked.add(input.id);
  } else if (node.kind === "run") {
    const agent = children.find((c) => c.kind === "agent" && c.name === node.name);
    if (agent) linked.add(agent.id);
  } else if (node.kind === "input") {
    for (const wf of children.filter((c) => c.kind === "workflow")) {
      for (const step of wf.children || []) {
        if (step.kind === "receive" && step.name === node.name) linked.add(step.id);
      }
    }
  } else if (node.kind === "agent") {
    for (const wf of children.filter((c) => c.kind === "workflow")) {
      for (const step of wf.children || []) {
        if (step.kind === "run" && step.name === node.name) linked.add(step.id);
      }
    }
  }
  return linked;
}

export function collectRefOptions(program, kind) {
  const children = program.children || [];
  if (kind === "run") {
    return children.filter((c) => c.kind === "agent" && c.name).map((c) => c.name);
  }
  if (kind === "receive") {
    return children.filter((c) => c.kind === "input" && c.name).map((c) => c.name);
  }
  return [];
}
