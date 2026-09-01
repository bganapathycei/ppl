import { BLOCKS } from "./schema.js";

export function uid() {
  return "n_" + Math.random().toString(36).slice(2, 10) + Math.random().toString(36).slice(2, 6);
}

const FACTORIES = {
  app: () => ({ name: "MyApplication" }),
  input: () => ({ name: "request" }),
  field: () => ({ name: "field", type: "TEXT" }),
  model_policy: () => ({
    name: "Default",
    reasoning: "reasoning-default",
    classification: "classification-default",
    extraction: "extraction-default",
    max_retries: "1",
    fallback: "fallback-default",
  }),
  guard: () => ({ name: "Safety" }),
  rule: () => ({ text: "NEVER execute sensitive actions without authorization" }),
  authorization: () => ({ name: "prod_change", requires: "production.write" }),
  budget: () => ({ max_cost: "0.10", max_latency: "5000ms", max_steps: "10" }),
  environment: () => ({ name: "production" }),
  knowledge: () => ({ name: "Docs" }),
  source: () => ({ name: "runbooks" }),
  memory: () => ({ name: "History", key: "request.id" }),
  memory_clause: () => ({ text: "READ items" }),
  tool: () => ({ name: "ITSM" }),
  action: () => ({ name: "create_ticket" }),
  tool_input: () => ({}),
  tool_output: () => ({}),
  agent: () => ({ name: "Classifier" }),
  agent_input: () => ({ name: "request" }),
  policy_ref: () => ({ name: "Default" }),
  use_knowledge: () => ({ name: "Docs" }),
  use_memory: () => ({ name: "History" }),
  classify: () => ({ target: "request.text" }),
  category: () => ({ name: "OTHER" }),
  extract: () => ({}),
  reason: () => ({ instruction: "determine the best next action", outputFields: [] }),
  consider: () => ({ text: "risk" }),
  output: () => ({}),
  workflow: () => ({ name: "Main" }),
  receive: () => ({ name: "request" }),
  run: () => ({ name: "Classifier" }),
  if: () => ({
    left: "Classifier.confidence",
    operator: "<",
    right: "0.90",
    elseIf: [],
    elseChildren: [],
  }),
  else_if: () => ({ left: "value", operator: "==", right: "TRUE" }),
  return: () => ({ value: "Classifier.category", literal: false }),
  human_approval: () => ({ question: "validate before continuing" }),
  option: () => ({ name: "APPROVE" }),
  parallel: () => ({}),
  join: () => ({ names: "" }),
  wait: () => ({ condition: "1s" }),
  checkpoint: () => ({ name: "save" }),
  call: () => ({ target: "ITSM.create_ticket" }),
  arg: () => ({ name: "title", value: '"Example"' }),
};

export function createNode(kind, extras = {}) {
  const node = { id: uid(), kind, children: [] };
  Object.assign(node, (FACTORIES[kind] || (() => ({})))(), extras);
  if (kind === "if") {
    node.elseIf = node.elseIf || [];
    node.elseChildren = node.elseChildren || [];
  }
  if (kind === "reason") node.outputFields = node.outputFields || [];
  return node;
}

export function emptyProgram() {
  return { id: uid(), kind: "program", children: [] };
}

export function helloWorldDocument() {
  return {
    id: uid(),
    kind: "program",
    children: [
      createNode("app", { name: "HelloAI" }),
      createNode("input", {
        name: "request",
        children: [createNode("field", { name: "text", type: "TEXT" })],
      }),
      createNode("agent", {
        name: "Classifier",
        children: [
          createNode("agent_input", { name: "request" }),
          createNode("classify", {
            target: "request.text",
            children: [
              createNode("category", { name: "GREETING" }),
              createNode("category", { name: "QUESTION" }),
              createNode("category", { name: "OTHER" }),
            ],
          }),
          createNode("output", {
            children: [
              createNode("field", { name: "category", type: "" }),
              createNode("field", { name: "confidence", type: "" }),
            ],
          }),
        ],
      }),
      createNode("workflow", {
        name: "Main",
        children: [
          createNode("receive", { name: "request" }),
          createNode("run", { name: "Classifier" }),
          createNode("return", { value: "Classifier.category", literal: false }),
        ],
      }),
    ],
  };
}

export function getSlot(node, slot) {
  if (!node) return null;
  if (slot === "children") {
    if (!node.children) node.children = [];
    return node.children;
  }
  if (slot === "elseIf") {
    if (!node.elseIf) node.elseIf = [];
    return node.elseIf;
  }
  if (slot === "elseChildren") {
    if (!node.elseChildren) node.elseChildren = [];
    return node.elseChildren;
  }
  if (slot === "outputFields") {
    if (!node.outputFields) node.outputFields = [];
    return node.outputFields;
  }
  return null;
}

export function walk(node, fn, parent = null, slot = null, index = -1) {
  fn(node, parent, slot, index);
  for (const spec of BLOCKS[node.kind]?.slots || []) {
    const list = getSlot(node, spec.name) || [];
    list.forEach((child, i) => walk(child, fn, node, spec.name, i));
  }
}

export function locate(root, id) {
  let found = null;
  walk(root, (node, parent, slot, index) => {
    if (node.id === id) found = { node, parent, slot, index };
  });
  return found;
}

export function getNode(root, id) {
  return locate(root, id)?.node || null;
}

export function contains(ancestor, id) {
  let hit = false;
  walk(ancestor, (node) => {
    if (node.id === id) hit = true;
  });
  return hit;
}

export function removeNode(root, id) {
  const found = locate(root, id);
  if (!found || !found.parent) return null;
  const list = getSlot(found.parent, found.slot);
  if (!list) return null;
  const [node] = list.splice(found.index, 1);
  return node;
}

export function insertNode(parent, slot, index, node) {
  const list = getSlot(parent, slot);
  if (!list) return false;
  const i = Math.max(0, Math.min(index, list.length));
  list.splice(i, 0, node);
  return true;
}

export function moveNode(root, nodeId, parentId, slot, index) {
  const moving = getNode(root, nodeId);
  const parent = getNode(root, parentId);
  if (!moving || !parent || moving.id === parent.id) return false;
  if (contains(moving, parentId)) return false;
  const before = locate(root, nodeId);
  removeNode(root, nodeId);
  let i = index;
  if (before && before.parent?.id === parentId && before.slot === slot && before.index < index) {
    i -= 1;
  }
  return insertNode(parent, slot, i, moving);
}

export function setProp(node, prop, value) {
  if (prop === "literal") node[prop] = Boolean(value);
  else node[prop] = value;
}

export function cloneDocument(doc) {
  return JSON.parse(JSON.stringify(doc));
}
