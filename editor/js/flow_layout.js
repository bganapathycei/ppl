// Pure auto-layout for the PPL flow canvas.
//
// Turns the editor document (AST) into absolutely positioned nodes plus edges.
// The document stays the single source of truth; this module never mutates it,
// which keeps `.ppl` codegen and round-tripping deterministic. Everything here
// is framework-free so it can be unit tested under plain Node.

import { BLOCKS } from "./schema.js";

export const FLOW = {
  nodeW: 220,
  nodeMinH: 58,
  lineH: 15,
  vGap: 34,
  hGap: 40,
  pad: 28,
  bandGap: 30,
  mergeR: 9,
};

const TONE_OF = {
  app: "app",
  det: "det",
  cog: "cog",
  hum: "hum",
  gov: "gov",
  ent: "ent",
};

export function tone(kind) {
  return TONE_OF[BLOCKS[kind]?.tone] || "det";
}

function truncate(text, max = 40) {
  const value = String(text ?? "").replace(/\s+/g, " ").trim();
  return value.length > max ? value.slice(0, max - 1) + "…" : value;
}

function conditionText(node) {
  const left = (node.left ?? "").toString().trim() || "left";
  const right = (node.right ?? "").toString().trim();
  return `${left} ${node.operator || "=="} ${right}`.trim();
}

// Primary + secondary lines shown inside a flow node.
export function summarize(node) {
  switch (node.kind) {
    case "app":
      return [node.name || "MyApplication"];
    case "input": {
      const fields = (node.children || [])
        .map((f) => `${f.name || "field"}${f.type ? ": " + f.type : ""}`)
        .slice(0, 4);
      return [node.name || "request", ...fields];
    }
    case "model_policy":
      return [node.name || "Default", node.reasoning ? `reasoning: ${node.reasoning}` : ""].filter(Boolean);
    case "guard":
      return [node.name || "Safety", ...(node.children || []).map((r) => truncate(r.text, 34)).slice(0, 3)];
    case "authorization":
      return [node.name || "auth", node.requires ? `requires ${node.requires}` : ""].filter(Boolean);
    case "budget":
      return [
        "limits",
        node.max_cost ? `cost ${node.max_cost}` : "",
        node.max_latency ? `latency ${node.max_latency}` : "",
        node.max_steps ? `steps ${node.max_steps}` : "",
      ].filter(Boolean);
    case "environment":
      return [node.name || "production", ...(node.children || []).map((r) => truncate(r.text, 34)).slice(0, 3)];
    case "knowledge":
      return [node.name || "Docs", ...(node.children || []).map((s) => `SOURCE ${s.name || "source"}`).slice(0, 4)];
    case "memory":
      return [node.name || "History", node.key ? `KEY ${node.key}` : ""].filter(Boolean);
    case "tool": {
      const lines = [];
      for (const child of node.children || []) {
        if (child.kind === "action") lines.push(`ACTION ${child.name || "action"}`);
      }
      return [node.name || "Tool", ...lines.slice(0, 4)];
    }
    case "agent": {
      const lines = [];
      for (const child of node.children || []) {
        if (child.kind === "agent_input") lines.push(`INPUT ${child.name || "request"}`);
        else if (child.kind === "policy_ref") lines.push(`POLICY ${child.name || "Default"}`);
        else if (child.kind === "use_knowledge") lines.push(`USE KNOWLEDGE ${child.name || "Docs"}`);
        else if (child.kind === "use_memory") lines.push(`USE MEMORY ${child.name || "History"}`);
        else if (child.kind === "classify") lines.push(`CLASSIFY ${truncate(child.target, 24)}`);
        else if (child.kind === "extract") lines.push("EXTRACT");
        else if (child.kind === "reason") lines.push(`REASON ${truncate(child.instruction, 22)}`);
        else if (child.kind === "output") {
          const names = (child.children || []).map((f) => f.name || "field").join(", ");
          lines.push(`OUTPUT ${truncate(names, 24)}`);
        }
      }
      return [node.name || "Agent", ...lines.slice(0, 6)];
    }
    case "workflow":
      return [node.name || "Main"];
    case "receive":
      return [node.name || "request"];
    case "run":
      return [node.name || "Agent"];
    case "let":
      return [`${node.name || "x"} = ${truncate(node.expr, 28) || "0"}`];
    case "print":
      return [truncate(node.expr, 36) || '"…"'];
    case "read":
      return [`${node.path || "file"} → ${node.var || "var"}`];
    case "write":
      return [`${node.path || "file"} ← ${truncate(node.expr, 20) || "expr"}`];
    case "for":
      return [`${node.item || "item"} in ${truncate(node.source, 24) || "list"}`];
    case "while":
      return [truncate(node.condition, 36) || "condition"];
    case "return":
      return [node.literal ? JSON.stringify(String(node.value ?? "")) : (node.value ?? "").toString() || "value"];
    case "if":
      return [conditionText(node)];
    case "human_approval":
      return [truncate(node.question, 38) || "approval", ...(node.children || []).map((o) => o.name || "OPTION").slice(0, 4)];
    case "parallel":
      return ["branches"];
    case "join":
      return [(node.names || "").trim() || "all branches"];
    case "wait":
      return [(node.condition || "").trim() || "1s"];
    case "checkpoint":
      return [(node.name || "").trim() || "save"];
    case "call": {
      const args = (node.children || [])
        .filter((a) => a.kind === "arg")
        .map((a) => `${a.name || "arg"} = ${truncate(a.value, 16)}`);
      return [node.target || "Tool.action", ...args.slice(0, 4)];
    }
    case "import":
      return [node.module || "stdlib.files"];
    case "prompt":
      return [node.name || "Template", ...(node.children || []).map((r) => truncate(r.text, 34)).slice(0, 3)];
    default:
      return [node.name || node.kind];
  }
}

function nodeHeight(lines) {
  const extra = Math.max(0, lines.length - 1);
  return Math.max(FLOW.nodeMinH, 30 + extra * FLOW.lineH + (lines.length ? 14 : 0));
}

function makeBox(node, { role = "node", selectable = true } = {}) {
  const lines = summarize(node);
  const keyword = BLOCKS[node.kind]?.keyword || node.kind.toUpperCase();
  return {
    kind: "box",
    id: node.id,
    nodeKind: node.kind,
    keyword,
    tone: tone(node.kind),
    title: lines[0] || "",
    lines: lines.slice(1),
    role,
    selectable,
    w: FLOW.nodeW,
    h: nodeHeight(lines),
  };
}

// A leaf produces a single box; ports are top-center / bottom-center.
// `terminal` marks a node that ends the path (RETURN), so callers omit the
// outgoing flow arrow.
function measureLeaf(box, terminal = false) {
  return {
    w: box.w,
    h: box.h,
    inX: box.w / 2,
    outX: box.w / 2,
    terminal,
    items: [{ ...box, x: 0, y: 0 }],
    edges: [],
  };
}

function offset(layout, dx, dy) {
  for (const item of layout.items) {
    item.x += dx;
    item.y += dy;
  }
  for (const edge of layout.edges) {
    edge.x1 += dx;
    edge.y1 += dy;
    edge.x2 += dx;
    edge.y2 += dy;
    if (edge.labelX != null) edge.labelX += dx;
    if (edge.labelY != null) edge.labelY += dy;
  }
  return layout;
}

function emptyBranchBox() {
  return {
    kind: "box",
    id: null,
    nodeKind: "pass",
    keyword: "PASS",
    tone: "det",
    title: "(empty)",
    lines: [],
    role: "ghost",
    selectable: false,
    w: 120,
    h: 38,
  };
}

// Vertical sequence of workflow steps, connected top-to-bottom.
function measureSequence(steps, ownerId, slot) {
  const child = (steps || []).map(measureStep);
  if (!child.length) {
    const leaf = measureLeaf(emptyBranchBox());
    leaf.terminal = false;
    return leaf;
  }
  const axis = Math.max(...child.map((c) => c.inX));
  let y = 0;
  const items = [];
  const edges = [];
  let width = 0;
  let prev = null;
  child.forEach((c) => {
    const dx = axis - c.inX;
    offset(c, dx, y);
    items.push(...c.items);
    edges.push(...c.edges);
    width = Math.max(width, dx + c.w);
    // No arrow out of a terminal (RETURN) step: the next sibling is unreachable.
    if (prev && !prev.terminal) {
      edges.push({ x1: prev.outAbsX, y1: prev.outAbsY, x2: axis, y2: y, kind: "flow" });
    }
    prev = { outAbsX: dx + c.outX, outAbsY: y + c.h, terminal: c.terminal };
    y += c.h + FLOW.vGap;
  });
  const height = y - FLOW.vGap;
  return {
    w: width,
    h: height,
    inX: axis,
    outX: prev.outAbsX,
    terminal: prev.terminal,
    items,
    edges,
  };
}

// Branch container shared by IF and PARALLEL: a header fans out to lanes that
// merge into a single point, so control flow reads as a real diagram. Lanes
// that terminate (all-RETURN) do not connect onward to the merge.
function measureBranches(headerBox, branches, terminal) {
  const header = measureLeaf(headerBox);
  const laneLayouts = branches.map((b) => b.layout);
  const totalW = laneLayouts.reduce((sum, l) => sum + l.w, 0) + FLOW.hGap * Math.max(0, laneLayouts.length - 1);
  const laneTop = header.h + FLOW.vGap + 14;
  const maxLaneH = Math.max(...laneLayouts.map((l) => l.h), 1);
  const hasMerge = branches.some((b) => !b.layout.terminal);

  const centerX = totalW / 2;
  const items = [];
  const edges = [];

  // Header centered over the lanes.
  offset(header, centerX - header.inX, 0);
  items.push(...header.items);
  edges.push(...header.edges);
  const headerOutX = centerX;
  const headerOutY = header.h;

  const mergeY = laneTop + maxLaneH + FLOW.vGap;

  let x = 0;
  branches.forEach((b) => {
    const lane = b.layout;
    const dx = x;
    offset(lane, dx, laneTop);
    items.push(...lane.items);
    edges.push(...lane.edges);
    const laneInX = dx + lane.inX;
    const laneOutX = dx + lane.outX;
    edges.push({
      x1: headerOutX,
      y1: headerOutY,
      x2: laneInX,
      y2: laneTop,
      kind: "branch",
      label: b.label || "",
      labelX: (headerOutX + laneInX) / 2,
      labelY: headerOutY + (laneTop - headerOutY) / 2,
    });
    if (hasMerge && !lane.terminal) {
      edges.push({ x1: laneOutX, y1: laneTop + lane.h, x2: centerX, y2: mergeY + FLOW.mergeR, kind: "merge" });
    }
    x += lane.w + FLOW.hGap;
  });

  if (hasMerge) {
    items.push({
      kind: "merge",
      role: "merge",
      selectable: false,
      w: FLOW.mergeR * 2,
      h: FLOW.mergeR * 2,
      x: centerX - FLOW.mergeR,
      y: mergeY,
    });
  }
  const height = hasMerge ? mergeY + FLOW.mergeR * 2 : laneTop + maxLaneH;
  return {
    w: totalW,
    h: height,
    inX: centerX,
    outX: centerX,
    terminal,
    items,
    edges,
  };
}

function measureIf(node) {
  const header = makeBox(node);
  const branches = [];
  branches.push({ label: "then", layout: measureSequence(node.children, node.id, "children") });
  for (const branch of node.elseIf || []) {
    branches.push({
      label: `else if ${conditionText(branch)}`,
      layout: measureSequence(branch.children, branch.id, "children"),
    });
  }
  const hasElse = (node.elseChildren || []).length > 0;
  branches.push({ label: "else", layout: measureSequence(node.elseChildren, node.id, "elseChildren") });
  // The whole IF terminates only if every path (including a real else) returns.
  const terminal = hasElse && branches.every((b) => b.layout.terminal);
  return measureBranches(header, branches, terminal);
}

function measureParallel(node) {
  const header = makeBox(node);
  const kids = node.children || [];
  const branches = kids.length
    ? kids.map((child, i) => ({ label: `branch ${i + 1}`, layout: measureStep(child) }))
    : [{ label: "branch", layout: measureSequence([], node.id, "children") }];
  return measureBranches(header, branches, false);
}

function measureStep(node) {
  if (node.kind === "if") return measureIf(node);
  if (node.kind === "parallel") return measureParallel(node);
  if (node.kind === "for" || node.kind === "while") {
    const header = makeBox(node);
    const body = measureSequence(node.children, node.id, "children");
    const chip = makeAddChip(node.id, "children", (node.children || []).length, "+ step");
    // Stack header → body → add chip as a compact loop block.
    const axis = Math.max(header.w / 2, body.inX, chip.w / 2);
    const headerLayout = measureLeaf(header);
    offset(headerLayout, axis - headerLayout.inX, 0);
    offset(body, axis - body.inX, header.h + FLOW.vGap);
    const chipY = header.h + FLOW.vGap + body.h + FLOW.vGap;
    const items = [
      ...headerLayout.items,
      ...body.items,
      { ...chip, x: axis - chip.w / 2, y: chipY },
    ];
    const edges = [
      ...body.edges,
      {
        x1: axis,
        y1: header.h,
        x2: axis,
        y2: header.h + FLOW.vGap,
        kind: "flow",
      },
    ];
    if (!body.terminal && body.items.length) {
      edges.push({
        x1: axis,
        y1: header.h + FLOW.vGap + body.h,
        x2: axis,
        y2: chipY,
        kind: "add",
      });
    }
    return {
      w: Math.max(header.w, body.w, chip.w),
      h: chipY + chip.h,
      inX: axis,
      outX: axis,
      terminal: false,
      items,
      edges,
    };
  }
  return measureLeaf(makeBox(node), node.kind === "return");
}

function makeAddChip(ownerId, slot, index, label) {
  return {
    kind: "add",
    id: `add__${ownerId}__${slot}`,
    role: "add",
    selectable: false,
    addOwner: ownerId,
    addSlot: slot,
    addIndex: index,
    title: label || "+ add",
    w: 150,
    h: 26,
  };
}

// Cross-links from workflow steps to declaration nodes (RECEIVE→INPUT, RUN→AGENT).
export function collectReferenceLinks(program) {
  const children = program.children || [];
  const inputByName = new Map();
  const agentByName = new Map();
  for (const child of children) {
    if (child.kind === "input" && child.name) inputByName.set(child.name, child.id);
    if (child.kind === "agent" && child.name) agentByName.set(child.name, child.id);
  }

  const links = [];
  function walk(steps) {
    for (const step of steps || []) {
      if (step.kind === "receive" && step.name && inputByName.has(step.name)) {
        links.push({ stepId: step.id, declId: inputByName.get(step.name) });
      }
      if (step.kind === "run" && step.name && agentByName.has(step.name)) {
        links.push({ stepId: step.id, declId: agentByName.get(step.name) });
      }
      if (step.kind === "if") {
        walk(step.children);
        for (const branch of step.elseIf || []) walk(branch.children);
        walk(step.elseChildren);
      }
      if (step.kind === "parallel") walk(step.children);
    }
  }

  for (const workflow of children.filter((child) => child.kind === "workflow")) {
    walk(workflow.children);
  }
  return links;
}

// Declaration cards laid out in a wrapping band (not control flow).
function measureBand(cards, maxWidth) {
  const items = [];
  let x = 0;
  let y = 0;
  let rowH = 0;
  let bandW = 0;
  for (const card of cards) {
    if (x > 0 && x + card.w > maxWidth) {
      x = 0;
      y += rowH + FLOW.vGap;
      rowH = 0;
    }
    items.push({ ...card, x, y });
    x += card.w + FLOW.hGap;
    rowH = Math.max(rowH, card.h);
    bandW = Math.max(bandW, x - FLOW.hGap);
  }
  return { items, w: bandW, h: y + rowH };
}

const CONTAINER = {
  headerH: 44,
  sectionLabelH: 22,
  zoneGap: 28,
  innerPad: 24,
  collapsedSectionH: 28,
};

function decorateItem(item, options) {
  if (!item.id || item.kind !== "box") return;
  const issues = options.issuesByNode?.get(item.id) || [];
  if (issues.length) {
    item.issueLevel = issues.some((i) => i.level === "error") ? "error" : "warn";
    item.issueTip = issues.map((i) => i.message).join("\n");
  }
  const trace = options.traceState || {};
  if (trace.executedIds?.has(item.id)) {
    item.traceStatus = item.id === trace.lastExecutedId ? "active" : "executed";
  }
  item.refHighlight = options.refLinked?.has(item.id) || item.id === options.hoverAstId;
  item.renamable = ["input", "agent", "workflow"].includes(item.nodeKind);
}

/**
 * Lay out the whole program inside an APP container frame.
 * @returns {{width:number,height:number,items:Array,edges:Array,container:Object}}
 */
export function layoutProgram(program, options = {}) {
  const maxWidth = options.maxWidth || 1100;
  const collapsed = options.collapsed || {};
  const declCollapsed = Boolean(collapsed.declarations);
  const wfCollapsed = Boolean(collapsed.workflows);
  const children = program.children || [];
  const appNode = children.find((child) => child.kind === "app");
  const appName = appNode?.name || "MyApplication";
  const appId = appNode?.id || null;
  const decls = children.filter((child) => child.kind !== "workflow" && child.kind !== "app");
  const workflows = children.filter((child) => child.kind === "workflow");

  const items = [];
  const edges = [];
  const innerX = FLOW.pad + CONTAINER.innerPad;
  const declLabelY = FLOW.pad + CONTAINER.headerH + 6;
  let cursorY = declLabelY + CONTAINER.sectionLabelH + 6;
  if (declCollapsed && decls.length) cursorY = declLabelY + CONTAINER.collapsedSectionH;

  if (decls.length && !declCollapsed) {
    const cards = decls.map((node) => makeBox(node, { role: node.kind === "agent" ? "agent" : "resource" }));
    const band = measureBand(cards, maxWidth - CONTAINER.innerPad * 2);
    for (const item of band.items) {
      item.x += innerX;
      item.y += cursorY;
      decorateItem(item, options);
      items.push(item);
    }
    cursorY += band.h + CONTAINER.zoneGap;
  }

  const workflowLabelY = workflows.length ? cursorY : null;
  if (workflows.length) {
    cursorY += declCollapsed && !decls.length ? 0 : CONTAINER.sectionLabelH + 6;
    if (wfCollapsed) cursorY = workflowLabelY + CONTAINER.collapsedSectionH;
  }

  if (!wfCollapsed) {
    for (const wf of workflows) {
      const headerBox = makeBox(wf, { role: "workflow-title" });
      const headerLayout = measureLeaf(headerBox);
      const body = measureSequence(wf.children, wf.id, "children");
      const axis = Math.max(headerLayout.inX, body.inX);

      offset(headerLayout, innerX + axis - headerLayout.inX, cursorY);
      for (const item of headerLayout.items) {
        decorateItem(item, options);
        items.push(item);
      }
      const headerOut = headerLayout.items[0];

      const bodyY = cursorY + headerBox.h + FLOW.vGap;
      offset(body, innerX + axis - body.inX, bodyY);
      for (const item of body.items) {
        decorateItem(item, options);
        items.push(item);
      }
      edges.push(...body.edges);
      edges.push({
        x1: headerOut.x + headerOut.w / 2,
        y1: headerOut.y + headerOut.h,
        x2: innerX + axis,
        y2: bodyY,
        kind: "flow",
      });

      const chip = makeAddChip(wf.id, "children", (wf.children || []).length, "+ step");
      const chipX = innerX + axis - chip.w / 2;
      const chipY = bodyY + body.h + FLOW.vGap;
      items.push({ ...chip, x: chipX, y: chipY });
      if (!body.terminal) {
        edges.push({
          x1: innerX + axis,
          y1: bodyY + body.h,
          x2: innerX + axis,
          y2: chipY,
          kind: "add",
        });
      }

      cursorY = chipY + chip.h + FLOW.bandGap;
    }
  }

  const progChip = makeAddChip(program.id, "children", children.length, "+ block");
  let maxRight = FLOW.pad + CONTAINER.innerPad;
  for (const item of items) maxRight = Math.max(maxRight, item.x + item.w);
  const containerW = Math.max(maxRight - FLOW.pad + CONTAINER.innerPad, FLOW.nodeW + FLOW.pad);
  const containerH = cursorY - FLOW.pad + CONTAINER.innerPad;
  const container = {
    kind: "container",
    role: "app-container",
    id: appId,
    appName,
    x: FLOW.pad,
    y: FLOW.pad,
    w: containerW,
    h: containerH,
    declLabelY,
    workflowLabelY,
    hasDeclarations: decls.length > 0,
    hasWorkflows: workflows.length > 0,
    declCount: decls.length,
    wfCount: workflows.length,
    declCollapsed,
    wfCollapsed,
    renamable: Boolean(appId),
    selectable: Boolean(appId),
  };

  items.push({ ...progChip, x: FLOW.pad, y: cursorY });
  cursorY += progChip.h + FLOW.pad;

  const idByAst = new Map(items.filter((item) => item.id).map((item) => [item.id, item]));
  if (!wfCollapsed) {
    for (const link of collectReferenceLinks(program)) {
      const step = idByAst.get(link.stepId);
      const decl = idByAst.get(link.declId);
      if (!step || !decl) continue;
      const active =
        options.hoverAstId &&
        (options.refLinked?.has(link.stepId) || options.refLinked?.has(link.declId));
      edges.push({
        x1: step.x + step.w / 2,
        y1: step.y,
        x2: decl.x + decl.w / 2,
        y2: decl.y + decl.h,
        kind: "ref",
        refActive: Boolean(active),
      });
    }
  }

  return {
    width: Math.max(containerW + FLOW.pad * 2, FLOW.nodeW + FLOW.pad * 2),
    height: containerH + FLOW.pad * 2,
    items,
    edges,
    container,
  };
}
