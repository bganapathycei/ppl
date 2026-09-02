export const TYPES = [
  "",
  "TEXT",
  "NUMBER",
  "INTEGER",
  "BOOLEAN",
  "CONFIDENCE",
  "CLASSIFICATION",
  "ID",
];

export const OPERATORS = [">=", "<=", "==", "!=", ">", "<"];

export const TOP_LEVEL = [
  "app",
  "import",
  "input",
  "prompt",
  "model_policy",
  "guard",
  "authorization",
  "budget",
  "environment",
  "knowledge",
  "memory",
  "tool",
  "agent",
  "workflow",
];

export const WORKFLOW_STEPS = [
  "receive",
  "run",
  "let",
  "print",
  "read",
  "write",
  "for",
  "while",
  "if",
  "return",
  "human_approval",
  "parallel",
  "join",
  "wait",
  "checkpoint",
  "call",
];

export const AGENT_BODY = [
  "agent_input",
  "policy_ref",
  "use_knowledge",
  "use_memory",
  "classify",
  "extract",
  "reason",
  "output",
];

export const TOOL_BODY = ["action", "tool_input", "tool_output"];

export const BLOCKS = {
  program: {
    keyword: "PROGRAM",
    tone: "app",
    palette: false,
    slots: [{ name: "children", label: "Program", accept: TOP_LEVEL }],
  },
  app: {
    keyword: "APP",
    tone: "app",
    unique: true,
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
  },
  input: {
    keyword: "INPUT",
    tone: "app",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
    slots: [{ name: "children", label: "Fields", accept: ["field"] }],
  },
  field: {
    keyword: "field",
    tone: "app",
    fields: [
      { prop: "name", kind: "text", placeholder: "name", grow: true },
      { prop: "type", kind: "type" },
    ],
  },
  model_policy: {
    keyword: "MODEL_POLICY",
    tone: "cog",
    fields: [
      { prop: "name", kind: "text", placeholder: "name" },
      { prop: "reasoning", kind: "text", placeholder: "reasoning" },
      { prop: "classification", kind: "text", placeholder: "classification" },
      { prop: "extraction", kind: "text", placeholder: "extraction" },
      { prop: "max_retries", kind: "text", placeholder: "retries" },
      { prop: "fallback", kind: "text", placeholder: "fallback" },
    ],
  },
  guard: {
    keyword: "GUARD",
    tone: "gov",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
    slots: [{ name: "children", label: "Rules", accept: ["rule"] }],
  },
  rule: {
    keyword: "rule",
    tone: "gov",
    fields: [{ prop: "text", kind: "text", placeholder: "rule text", grow: true }],
  },
  authorization: {
    keyword: "AUTHORIZATION",
    tone: "gov",
    fields: [
      { prop: "name", kind: "text", placeholder: "name", grow: true },
      { prop: "requires", kind: "text", placeholder: "REQUIRES" },
    ],
  },
  budget: {
    keyword: "BUDGET",
    tone: "gov",
    fields: [
      { prop: "max_cost", kind: "text", placeholder: "max_cost" },
      { prop: "max_latency", kind: "text", placeholder: "max_latency" },
      { prop: "max_steps", kind: "text", placeholder: "max_steps" },
    ],
  },
  environment: {
    keyword: "ENVIRONMENT",
    tone: "gov",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
    slots: [{ name: "children", label: "Body", accept: ["rule"] }],
  },
  knowledge: {
    keyword: "KNOWLEDGE",
    tone: "ent",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
    slots: [{ name: "children", label: "Sources", accept: ["source"] }],
  },
  source: {
    keyword: "SOURCE",
    tone: "ent",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
  },
  memory: {
    keyword: "MEMORY",
    tone: "ent",
    fields: [
      { prop: "name", kind: "text", placeholder: "name", grow: true },
      { prop: "key", kind: "text", placeholder: "KEY" },
    ],
    slots: [{ name: "children", label: "Clauses", accept: ["memory_clause"] }],
  },
  memory_clause: {
    keyword: "clause",
    tone: "ent",
    fields: [{ prop: "text", kind: "text", placeholder: "READ / WRITE …", grow: true }],
  },
  tool: {
    keyword: "TOOL",
    tone: "ent",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
    slots: [{ name: "children", label: "Body", accept: TOOL_BODY }],
  },
  action: {
    keyword: "ACTION",
    tone: "ent",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
  },
  tool_input: {
    keyword: "INPUT",
    tone: "ent",
    slots: [{ name: "children", label: "Fields", accept: ["field"] }],
  },
  tool_output: {
    keyword: "OUTPUT",
    tone: "ent",
    slots: [{ name: "children", label: "Fields", accept: ["field"] }],
  },
  agent: {
    keyword: "AGENT",
    tone: "cog",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
    slots: [{ name: "children", label: "Body", accept: AGENT_BODY }],
  },
  agent_input: {
    keyword: "INPUT",
    tone: "cog",
    fields: [{ prop: "name", kind: "text", placeholder: "binding", grow: true }],
  },
  policy_ref: {
    keyword: "POLICY",
    tone: "cog",
    fields: [{ prop: "name", kind: "text", placeholder: "policy", grow: true }],
  },
  use_knowledge: {
    keyword: "USE KNOWLEDGE",
    tone: "cog",
    fields: [{ prop: "name", kind: "text", placeholder: "knowledge", grow: true }],
  },
  use_memory: {
    keyword: "USE MEMORY",
    tone: "cog",
    fields: [{ prop: "name", kind: "text", placeholder: "memory", grow: true }],
  },
  classify: {
    keyword: "CLASSIFY",
    tone: "cog",
    fields: [{ prop: "target", kind: "text", placeholder: "target AS", grow: true }],
    slots: [{ name: "children", label: "Categories", accept: ["category"] }],
  },
  category: {
    keyword: "category",
    tone: "cog",
    fields: [{ prop: "name", kind: "text", placeholder: "NAME", grow: true }],
  },
  extract: {
    keyword: "EXTRACT",
    tone: "cog",
    slots: [{ name: "children", label: "Fields", accept: ["field"] }],
  },
  reason: {
    keyword: "REASON",
    tone: "cog",
    fields: [{ prop: "instruction", kind: "textarea", placeholder: "objective", grow: true }],
    slots: [
      { name: "children", label: "Consider", accept: ["consider"] },
      { name: "outputFields", label: "Output schema", accept: ["field"] },
    ],
  },
  consider: {
    keyword: "consider",
    tone: "cog",
    fields: [{ prop: "text", kind: "text", placeholder: "factor", grow: true }],
  },
  output: {
    keyword: "OUTPUT",
    tone: "cog",
    slots: [{ name: "children", label: "Fields", accept: ["field"] }],
  },
  workflow: {
    keyword: "WORKFLOW",
    tone: "det",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
    slots: [{ name: "children", label: "Steps", accept: WORKFLOW_STEPS }],
  },
  receive: {
    keyword: "RECEIVE",
    tone: "det",
    fields: [{ prop: "name", kind: "text", placeholder: "input", grow: true }],
  },
  run: {
    keyword: "RUN",
    tone: "det",
    fields: [{ prop: "name", kind: "text", placeholder: "agent", grow: true }],
  },
  let: {
    keyword: "LET",
    tone: "det",
    fields: [
      { prop: "name", kind: "text", placeholder: "variable" },
      { prop: "expr", kind: "text", placeholder: "expression", grow: true },
    ],
  },
  print: {
    keyword: "PRINT",
    tone: "det",
    fields: [{ prop: "expr", kind: "text", placeholder: "expression", grow: true }],
  },
  read: {
    keyword: "READ",
    tone: "det",
    fields: [
      { prop: "path", kind: "text", placeholder: "path" },
      { prop: "var", kind: "text", placeholder: "variable" },
    ],
  },
  write: {
    keyword: "WRITE",
    tone: "det",
    fields: [
      { prop: "path", kind: "text", placeholder: "path" },
      { prop: "expr", kind: "text", placeholder: "expression", grow: true },
    ],
  },
  for: {
    keyword: "FOR",
    tone: "det",
    fields: [
      { prop: "item", kind: "text", placeholder: "item" },
      { prop: "source", kind: "text", placeholder: "list expr" },
    ],
    slots: [{ name: "children", label: "Body", accept: WORKFLOW_STEPS }],
  },
  while: {
    keyword: "WHILE",
    tone: "det",
    fields: [{ prop: "condition", kind: "text", placeholder: "condition DO", grow: true }],
    slots: [{ name: "children", label: "Body", accept: WORKFLOW_STEPS }],
  },
  import: {
    keyword: "IMPORT",
    tone: "app",
    fields: [{ prop: "module", kind: "text", placeholder: "stdlib.files", grow: true }],
  },
  prompt: {
    keyword: "PROMPT",
    tone: "cog",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
    slots: [{ name: "children", label: "Template", accept: ["rule"] }],
  },
  if: {
    keyword: "IF",
    tone: "det",
    fields: [
      { prop: "left", kind: "text", placeholder: "left" },
      { prop: "operator", kind: "operator" },
      { prop: "right", kind: "text", placeholder: "right" },
    ],
    slots: [
      { name: "children", label: "Then", accept: WORKFLOW_STEPS },
      { name: "elseIf", label: "Else If", accept: ["else_if"] },
      { name: "elseChildren", label: "Else", accept: WORKFLOW_STEPS },
    ],
  },
  else_if: {
    keyword: "ELSE IF",
    tone: "det",
    fields: [
      { prop: "left", kind: "text", placeholder: "left" },
      { prop: "operator", kind: "operator" },
      { prop: "right", kind: "text", placeholder: "right" },
    ],
    slots: [{ name: "children", label: "Steps", accept: WORKFLOW_STEPS }],
  },
  return: {
    keyword: "RETURN",
    tone: "det",
    fields: [
      { prop: "value", kind: "text", placeholder: "value or path", grow: true },
      { prop: "literal", kind: "check", label: "literal" },
    ],
  },
  human_approval: {
    keyword: "HUMAN_APPROVAL",
    tone: "hum",
    fields: [{ prop: "question", kind: "text", placeholder: "question", grow: true }],
    slots: [{ name: "children", label: "Options", accept: ["option"] }],
  },
  option: {
    keyword: "option",
    tone: "hum",
    fields: [{ prop: "name", kind: "text", placeholder: "APPROVE", grow: true }],
  },
  parallel: {
    keyword: "PARALLEL",
    tone: "det",
    slots: [{ name: "children", label: "Branches", accept: WORKFLOW_STEPS }],
  },
  join: {
    keyword: "JOIN",
    tone: "det",
    fields: [{ prop: "names", kind: "text", placeholder: "names", grow: true }],
  },
  wait: {
    keyword: "WAIT",
    tone: "det",
    fields: [{ prop: "condition", kind: "text", placeholder: "1s | path | file:…", grow: true }],
  },
  checkpoint: {
    keyword: "CHECKPOINT",
    tone: "det",
    fields: [{ prop: "name", kind: "text", placeholder: "name", grow: true }],
  },
  call: {
    keyword: "CALL",
    tone: "det",
    fields: [{ prop: "target", kind: "text", placeholder: "Tool.action", grow: true }],
    slots: [{ name: "children", label: "Args", accept: ["arg"] }],
  },
  arg: {
    keyword: "arg",
    tone: "det",
    fields: [
      { prop: "name", kind: "text", placeholder: "name" },
      { prop: "value", kind: "text", placeholder: "value", grow: true },
    ],
  },
};

export const PALETTE_GROUPS = [
  {
    id: "application",
    title: "Application",
    kinds: ["app", "import", "input", "field", "prompt", "model_policy"],
  },
  {
    id: "cognitive",
    title: "Cognitive",
    kinds: [
      "agent",
      "agent_input",
      "policy_ref",
      "use_knowledge",
      "use_memory",
      "classify",
      "category",
      "extract",
      "reason",
      "consider",
      "output",
    ],
  },
  {
    id: "orchestration",
    title: "Orchestration",
    kinds: [
      "workflow",
      "receive",
      "run",
      "let",
      "print",
      "read",
      "write",
      "for",
      "while",
      "if",
      "else_if",
      "return",
      "parallel",
      "join",
      "wait",
      "checkpoint",
      "call",
      "arg",
      "human_approval",
      "option",
    ],
  },
  {
    id: "enterprise",
    title: "Enterprise",
    kinds: [
      "knowledge",
      "source",
      "memory",
      "memory_clause",
      "tool",
      "action",
      "tool_input",
      "tool_output",
      "guard",
      "rule",
      "authorization",
      "budget",
      "environment",
    ],
  },
];

export function slotSpec(kind, slot) {
  return (BLOCKS[kind]?.slots || []).find((item) => item.name === slot) || null;
}

export function accepts(parent, slot, childKind, options = {}) {
  if (!parent) return false;
  const spec = slotSpec(parent.kind, slot);
  if (!spec) return false;
  if (!spec.accept.includes(childKind)) return false;
  if (childKind === "app" && parent.kind === "program") {
    const others = (parent.children || []).filter(
      (child) => child.kind === "app" && child.id !== options.movingId,
    );
    if (others.length) return false;
  }
  return true;
}

export function defaultSlot(parentKind, childKind) {
  for (const spec of BLOCKS[parentKind]?.slots || []) {
    if (spec.accept.includes(childKind)) return spec.name;
  }
  return null;
}
