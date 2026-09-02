function indent(level) {
  return "    ".repeat(level);
}

function fieldLine(node) {
  const name = (node.name || "").trim() || "field";
  const type = (node.type || "").trim();
  return type ? `${name}: ${type}` : name;
}

function emitList(nodes, level, emitNode) {
  return (nodes || []).map((node) => emitNode(node, level)).filter(Boolean).join("\n");
}

function emitReason(node, level) {
  const pad = indent(level);
  const inner = indent(level + 1);
  const lines = [`${pad}REASON`];
  const instruction = (node.instruction || "").trim();
  if (instruction) lines.push(`${inner}${instruction}`);
  const considers = (node.children || []).filter((child) => child.kind === "consider");
  if (considers.length) {
    lines.push(`${inner}consider:`);
    for (const item of considers) {
      lines.push(`${indent(level + 2)}${(item.text || "").trim() || "factor"}`);
    }
  }
  const fields = node.outputFields || [];
  if (fields.length) {
    lines.push(`${inner}OUTPUT:`);
    for (const field of fields) lines.push(`${indent(level + 2)}${fieldLine(field)}`);
  }
  return lines.join("\n");
}

function emitIf(node, level) {
  const pad = indent(level);
  const cond = `${node.left || "left"} ${node.operator || "=="} ${node.right ?? ""}`.trim();
  const lines = [`${pad}IF ${cond}`];
  const thenBody = emitList(node.children, level + 1, emitStep);
  if (thenBody) lines.push(thenBody);
  for (const branch of node.elseIf || []) {
    const bcond = `${branch.left || "left"} ${branch.operator || "=="} ${branch.right ?? ""}`.trim();
    lines.push(`${pad}ELSE IF ${bcond}`);
    const body = emitList(branch.children, level + 1, emitStep);
    if (body) lines.push(body);
  }
  if ((node.elseChildren || []).length) {
    lines.push(`${pad}ELSE`);
    const body = emitList(node.elseChildren, level + 1, emitStep);
    if (body) lines.push(body);
  }
  return lines.join("\n");
}

function emitStep(node, level) {
  const pad = indent(level);
  switch (node.kind) {
    case "let":
      return `${pad}LET ${node.name || "x"} = ${node.expr || "0"}`;
    case "print":
      return `${pad}PRINT ${node.expr || ""}`;
    case "read":
      return `${pad}READ ${node.path || "file.txt"} INTO ${node.var || "content"}`;
    case "write":
      return `${pad}WRITE ${node.path || "file.txt"} FROM ${node.expr || "content"}`;
    case "for": {
      const lines = [`${pad}FOR ${node.item || "item"} IN ${node.source || "items"} DO`];
      const body = emitList(node.children, level + 1, emitStep);
      if (body) lines.push(body);
      return lines.join("\n");
    }
    case "while": {
      const lines = [`${pad}WHILE ${node.condition || "TRUE"} DO`];
      const body = emitList(node.children, level + 1, emitStep);
      if (body) lines.push(body);
      return lines.join("\n");
    }
    case "receive":
      return `${pad}RECEIVE ${node.name || "request"}`;
    case "run":
      return `${pad}RUN ${node.name || "Agent"}`;
    case "return": {
      const raw = node.value ?? "";
      const value = node.literal ? JSON.stringify(String(raw)) : raw;
      return `${pad}RETURN ${value}`;
    }
    case "if":
      return emitIf(node, level);
    case "human_approval": {
      const lines = [`${pad}HUMAN_APPROVAL`];
      const question = (node.question || "").trim();
      if (question) {
        lines.push(`${indent(level + 1)}QUESTION:`);
        lines.push(`${indent(level + 2)}${question}`);
      }
      const options = (node.children || []).filter((child) => child.kind === "option");
      if (options.length) {
        lines.push(`${indent(level + 1)}OPTIONS:`);
        for (const option of options) {
          lines.push(`${indent(level + 2)}${(option.name || "").trim() || "APPROVE"}`);
        }
      }
      return lines.join("\n");
    }
    case "parallel": {
      const lines = [`${pad}PARALLEL`];
      const body = emitList(node.children, level + 1, emitStep);
      if (body) lines.push(body);
      return lines.join("\n");
    }
    case "join": {
      const names = (node.names || "").trim();
      return names ? `${pad}JOIN ${names}` : `${pad}JOIN`;
    }
    case "wait": {
      const condition = (node.condition || "").trim();
      return condition ? `${pad}WAIT ${condition}` : `${pad}WAIT`;
    }
    case "checkpoint": {
      const name = (node.name || "").trim();
      return name ? `${pad}CHECKPOINT ${name}` : `${pad}CHECKPOINT`;
    }
    case "call": {
      const lines = [`${pad}CALL ${node.target || "Tool.action"}`];
      for (const arg of node.children || []) {
        if (arg.kind !== "arg") continue;
        lines.push(`${indent(level + 1)}${arg.name || "arg"} = ${arg.value ?? ""}`);
      }
      return lines.join("\n");
    }
    default:
      return "";
  }
}

function emitDecl(node) {
  switch (node.kind) {
    case "app":
      return `APP ${node.name || "MyApplication"}`;
    case "import":
      return `IMPORT ${node.module || "stdlib.files"}`;
    case "prompt": {
      const lines = [`PROMPT ${node.name || "Template"}`];
      for (const rule of node.children || []) lines.push(`${indent(1)}${(rule.text || "").trim()}`);
      return lines.join("\n");
    }
    case "input": {
      const lines = [`INPUT ${node.name || "request"}`];
      for (const field of node.children || []) lines.push(`${indent(1)}${fieldLine(field)}`);
      return lines.join("\n");
    }
    case "model_policy": {
      const lines = [`MODEL_POLICY ${node.name || "Default"}`];
      if (node.reasoning) lines.push(`${indent(1)}reasoning: ${node.reasoning}`);
      if (node.classification) lines.push(`${indent(1)}classification: ${node.classification}`);
      if (node.extraction) lines.push(`${indent(1)}extraction: ${node.extraction}`);
      if (node.max_retries !== "" && node.max_retries != null) {
        lines.push(`${indent(1)}max_retries: ${node.max_retries}`);
      }
      if (node.fallback) lines.push(`${indent(1)}fallback: ${node.fallback}`);
      return lines.join("\n");
    }
    case "guard": {
      const lines = [`GUARD ${node.name || "Safety"}`];
      for (const rule of node.children || []) {
        lines.push(`${indent(1)}${(rule.text || "").trim()}`);
      }
      return lines.join("\n");
    }
    case "authorization": {
      const lines = [`AUTHORIZATION ${node.name || "auth"}`];
      if (node.requires) lines.push(`${indent(1)}REQUIRES ${node.requires}`);
      return lines.join("\n");
    }
    case "budget": {
      const lines = ["BUDGET"];
      if (node.max_cost) lines.push(`${indent(1)}max_cost: ${node.max_cost}`);
      if (node.max_latency) lines.push(`${indent(1)}max_latency: ${node.max_latency}`);
      if (node.max_steps) lines.push(`${indent(1)}max_steps: ${node.max_steps}`);
      return lines.join("\n");
    }
    case "environment": {
      const lines = [`ENVIRONMENT ${node.name || "production"}`];
      for (const rule of node.children || []) {
        lines.push(`${indent(1)}${(rule.text || "").trim()}`);
      }
      return lines.join("\n");
    }
    case "knowledge": {
      const lines = [`KNOWLEDGE ${node.name || "Docs"}`];
      for (const source of node.children || []) {
        lines.push(`${indent(1)}SOURCE ${(source.name || "").trim() || "source"}`);
      }
      return lines.join("\n");
    }
    case "memory": {
      const lines = [`MEMORY ${node.name || "History"}`];
      if (node.key) lines.push(`${indent(1)}KEY ${node.key}`);
      for (const clause of node.children || []) {
        lines.push(`${indent(1)}${(clause.text || "").trim()}`);
      }
      return lines.join("\n");
    }
    case "tool": {
      const lines = [`TOOL ${node.name || "Tool"}`];
      for (const child of node.children || []) {
        if (child.kind === "action") lines.push(`${indent(1)}ACTION ${child.name || "action"}`);
        if (child.kind === "tool_input") {
          lines.push(`${indent(1)}INPUT`);
          for (const field of child.children || []) lines.push(`${indent(2)}${fieldLine(field)}`);
        }
        if (child.kind === "tool_output") {
          lines.push(`${indent(1)}OUTPUT`);
          for (const field of child.children || []) lines.push(`${indent(2)}${fieldLine(field)}`);
        }
      }
      return lines.join("\n");
    }
    case "agent": {
      const lines = [`AGENT ${node.name || "Agent"}`];
      for (const child of node.children || []) {
        if (child.kind === "agent_input") lines.push(`${indent(1)}INPUT ${child.name || "request"}`);
        else if (child.kind === "policy_ref") lines.push(`${indent(1)}POLICY ${child.name || "Default"}`);
        else if (child.kind === "use_knowledge") lines.push(`${indent(1)}USE KNOWLEDGE ${child.name || "Docs"}`);
        else if (child.kind === "use_memory") lines.push(`${indent(1)}USE MEMORY ${child.name || "History"}`);
        else if (child.kind === "classify") {
          lines.push(`${indent(1)}CLASSIFY ${child.target || "request.text"} AS`);
          for (const cat of child.children || []) {
            lines.push(`${indent(2)}${(cat.name || "").trim() || "OTHER"}`);
          }
        } else if (child.kind === "extract") {
          lines.push(`${indent(1)}EXTRACT`);
          for (const field of child.children || []) lines.push(`${indent(2)}${fieldLine(field)}`);
        } else if (child.kind === "reason") {
          lines.push(emitReason(child, 1));
        } else if (child.kind === "output") {
          lines.push(`${indent(1)}OUTPUT`);
          for (const field of child.children || []) lines.push(`${indent(2)}${fieldLine(field)}`);
        }
      }
      return lines.join("\n");
    }
    case "workflow": {
      const lines = [`WORKFLOW ${node.name || "Main"}`];
      const body = emitList(node.children, 1, emitStep);
      if (body) lines.push(body);
      return lines.join("\n");
    }
    default:
      return "";
  }
}

export function generatePpl(program) {
  const parts = [];
  for (const child of program.children || []) {
    const text = emitDecl(child);
    if (text) parts.push(text);
  }
  return parts.join("\n\n") + (parts.length ? "\n" : "");
}

export function appName(program) {
  const app = (program.children || []).find((child) => child.kind === "app");
  return (app?.name || "program").replace(/[^\w.-]+/g, "_") || "program";
}
