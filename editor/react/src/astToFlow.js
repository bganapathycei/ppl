// Convert a PPL document (AST) into React Flow nodes/edges, laid out with
// dagre. The AST stays the source of truth (shared parse/codegen keep `.ppl`
// round-tripping); this module derives a control-flow graph:
//   - APP frames declarations and workflows inside one visual container
//   - workflow steps chain top-to-bottom
//   - IF / PARALLEL fan out into labeled branches that merge (RETURN paths
//     terminate and do not merge onward)
//   - dashed reference edges link RECEIVE/RUN steps to INPUT/AGENT declarations
import dagre from "@dagrejs/dagre";
import { summarize, tone, collectReferenceLinks } from "../../js/flow_layout.js";
import { BLOCKS } from "../../js/schema.js";

const NODE_W = 224;
const H_GAP = 32;
const V_GAP = 26;
const INNER_PAD = 24;
const HEADER_H = 44;
const SECTION_LABEL_H = 22;
const ZONE_GAP = 28;
const DECL_MAX_W = 900;
const WF_GAP = 40;
const OUTER_PAD = 20;
const COLLAPSED_SECTION_H = 28;

function nodeHeight(lines) {
  return 44 + Math.max(0, lines.length) * 16;
}

function makeNode(node, role) {
  const [title, ...lines] = summarize(node);
  return {
    id: node.id,
    type: "ppl",
    data: {
      astId: node.id,
      kind: node.kind,
      keyword: BLOCKS[node.kind]?.keyword || node.kind.toUpperCase(),
      tone: tone(node.kind),
      title: title || "",
      lines,
      role,
      renamable: ["app", "input", "agent", "workflow"].includes(node.kind),
    },
    position: { x: 0, y: 0 },
    width: NODE_W,
    height: nodeHeight(lines),
  };
}

function decorateNodeData(data, astId, options) {
  const issues = options.issuesByNode?.get(astId) || [];
  data.issues = issues;
  if (issues.length) {
    data.issueLevel = issues.some((i) => i.level === "error") ? "error" : "warn";
    data.issueTip = issues.map((i) => i.message).join("\n");
  }
  const trace = options.traceState || {};
  if (trace.executedIds?.has(astId)) {
    data.traceStatus = astId === trace.lastExecutedId ? "active" : "executed";
  }
  data.refHighlight = options.refLinked?.has(astId) || astId === options.hoverAstId;
}

function conditionLabel(node) {
  const left = (node.left ?? "").toString().trim() || "left";
  const right = (node.right ?? "").toString().trim();
  return `${left} ${node.operator || "=="} ${right}`.trim();
}

let ghostSeq = 0;

function ghostNode() {
  const id = `ghost_${ghostSeq++}`;
  return {
    id,
    type: "ppl",
    data: { astId: null, kind: "pass", keyword: "PASS", tone: "det", title: "(empty)", lines: [], role: "ghost" },
    position: { x: 0, y: 0 },
    width: 120,
    height: 40,
  };
}

function edge(source, target, label, kind = "flow") {
  return {
    id: `${source}->${target}-${label || kind}`,
    source,
    target,
    label: label || undefined,
    data: { kind },
  };
}

function emitSequence(steps, options) {
  const nodes = [];
  const edges = [];
  let entry = null;
  let openEnds = [];
  for (const step of steps || []) {
    const r = emitStep(step, options);
    nodes.push(...r.nodes);
    edges.push(...r.edges);
    if (entry === null) entry = r.entry;
    for (const end of openEnds) edges.push(edge(end, r.entry));
    openEnds = r.exits;
  }
  if (entry === null) {
    const ghost = ghostNode();
    return { nodes: [ghost], edges: [], entry: ghost.id, exits: [ghost.id] };
  }
  return { nodes, edges, entry, exits: openEnds };
}

function emitBranches(headerNode, branches, options) {
  const nodes = [headerNode];
  const edges = [];
  const exits = [];
  for (const branch of branches) {
    const seq = emitSequence(branch.steps, options);
    nodes.push(...seq.nodes);
    edges.push(...seq.edges);
    edges.push(edge(headerNode.id, seq.entry, branch.label, "branch"));
    exits.push(...seq.exits);
  }
  return { nodes, edges, entry: headerNode.id, exits };
}

function emitStep(node, options) {
  if (node.kind === "if") {
    const branches = [{ label: "then", steps: node.children }];
    for (const b of node.elseIf || []) branches.push({ label: `else if ${conditionLabel(b)}`, steps: b.children });
    branches.push({ label: "else", steps: node.elseChildren });
    const header = makeNode(node, "step");
    decorateNodeData(header.data, node.id, options);
    return emitBranches(header, branches, options);
  }
  if (node.kind === "parallel") {
    const kids = node.children || [];
    const branches = kids.length
      ? kids.map((child, i) => ({ label: `branch ${i + 1}`, steps: [child] }))
      : [{ label: "branch", steps: [] }];
    const header = makeNode(node, "step");
    decorateNodeData(header.data, node.id, options);
    return emitBranches(header, branches, options);
  }
  const single = makeNode(node, "step");
  decorateNodeData(single.data, node.id, options);
  return { nodes: [single], edges: [], entry: single.id, exits: node.kind === "return" ? [] : [single.id] };
}

function layoutControlFlow(nodes, edges) {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: "TB", nodesep: 42, ranksep: 46, marginx: 8, marginy: 8 });
  g.setDefaultEdgeLabel(() => ({}));
  for (const node of nodes) g.setNode(node.id, { width: node.width, height: node.height });
  for (const e of edges) g.setEdge(e.source, e.target);
  dagre.layout(g);
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const node of nodes) {
    const p = g.node(node.id);
    node.position = { x: p.x - node.width / 2, y: p.y - node.height / 2 };
    minX = Math.min(minX, node.position.x);
    maxX = Math.max(maxX, node.position.x + node.width);
    minY = Math.min(minY, node.position.y);
    maxY = Math.max(maxY, node.position.y + node.height);
  }
  return { minX, maxX, minY, maxY, w: maxX - minX, h: maxY - minY };
}

function layoutDeclarationBand(declNodes, startX, startY) {
  let x = startX;
  let y = startY;
  let rowH = 0;
  let maxX = startX;
  let maxY = startY;
  const bandMaxW = DECL_MAX_W - INNER_PAD * 2;

  for (const node of declNodes) {
    if (x > startX && x + node.width > startX + bandMaxW) {
      x = startX;
      y += rowH + V_GAP;
      rowH = 0;
    }
    node.position = { x, y };
    x += node.width + H_GAP;
    rowH = Math.max(rowH, node.height);
    maxX = Math.max(maxX, x - H_GAP);
    maxY = Math.max(maxY, y + node.height);
  }

  const w = Math.max(maxX - startX, NODE_W);
  const h = declNodes.length ? maxY - startY + rowH : 0;
  return { w, h };
}

function offsetNodes(nodes, dx, dy) {
  for (const node of nodes) {
    node.position = { x: node.position.x + dx, y: node.position.y + dy };
  }
}

function layoutWorkflows(workflows, startX, startY, options) {
  const allNodes = [];
  const allEdges = [];
  let y = startY;
  let maxW = 0;

  for (const wf of workflows) {
    const header = makeNode(wf, "workflow-title");
    decorateNodeData(header.data, wf.id, options);
    const body = emitSequence(wf.children, options);
    const wfNodes = [header, ...body.nodes];
    const wfEdges = [edge(header.id, body.entry), ...body.edges];
    const bounds = layoutControlFlow(wfNodes, wfEdges);
    offsetNodes(wfNodes, startX - bounds.minX, y - bounds.minY);
    allNodes.push(...wfNodes);
    allEdges.push(...wfEdges);
    maxW = Math.max(maxW, bounds.w);
    y += bounds.h + WF_GAP;
  }

  const h = workflows.length ? y - startY - WF_GAP : 0;
  return { nodes: allNodes, edges: allEdges, w: maxW, h };
}

function buildReferenceEdges(links, flowIdByAstId) {
  const refEdges = [];
  for (const link of links) {
    const source = flowIdByAstId.get(link.stepId);
    const target = flowIdByAstId.get(link.declId);
    if (source && target) refEdges.push(edge(source, target, undefined, "ref"));
  }
  return refEdges;
}

export function buildFlow(program, options = {}) {
  ghostSeq = 0;
  const collapsed = options.collapsed || {};
  const children = program.children || [];
  const appNode = children.find((c) => c.kind === "app") || {
    id: `app-placeholder-${program.id}`,
    kind: "app",
    name: "MyApplication",
  };
  const decls = children.filter((c) => c.kind !== "workflow" && c.kind !== "app");
  const workflows = children.filter((c) => c.kind === "workflow");

  const containerId = `app-container-${appNode.id}`;
  const contentX = INNER_PAD;
  const declLabelY = HEADER_H + 6;
  const declCollapsed = Boolean(collapsed.declarations);
  const wfCollapsed = Boolean(collapsed.workflows);

  let declStartY = declLabelY + SECTION_LABEL_H + 6;
  if (declCollapsed) declStartY = declLabelY + COLLAPSED_SECTION_H;

  const declNodes = declCollapsed
    ? []
    : decls.map((node) => {
        const card = makeNode(node, node.kind === "agent" ? "agent" : "resource");
        decorateNodeData(card.data, node.id, options);
        return card;
      });
  const declBand = declCollapsed ? { w: NODE_W, h: 0 } : layoutDeclarationBand(declNodes, contentX, declStartY);

  let workflowLabelY = null;
  let workflowStartY = declStartY;
  if (decls.length) {
    workflowLabelY = declStartY + declBand.h + (declCollapsed ? 0 : ZONE_GAP);
    workflowStartY = workflowLabelY + (workflows.length ? SECTION_LABEL_H + 6 : 0);
  } else if (workflows.length) {
    workflowLabelY = declLabelY;
    workflowStartY = declLabelY + SECTION_LABEL_H + 6;
  }
  if (wfCollapsed && workflows.length) {
    workflowStartY = workflowLabelY + COLLAPSED_SECTION_H;
  }

  const wfLayout = wfCollapsed
    ? { nodes: [], edges: [], w: NODE_W, h: workflows.length ? COLLAPSED_SECTION_H : 0 }
    : layoutWorkflows(workflows, contentX, workflowStartY, options);

  const contentW = Math.max(declBand.w, wfLayout.w, NODE_W);
  const contentH = Math.max(
    declCollapsed && decls.length ? declStartY + COLLAPSED_SECTION_H : declStartY + declBand.h,
    workflows.length
      ? wfCollapsed
        ? workflowLabelY + COLLAPSED_SECTION_H
        : workflowStartY + wfLayout.h
      : declStartY,
  );

  const containerW = contentW + INNER_PAD * 2;
  const containerH = contentH + INNER_PAD;
  const childNodes = [...declNodes, ...wfLayout.nodes];

  const flowIdByAstId = new Map();
  for (const node of childNodes) {
    if (node.data.astId) flowIdByAstId.set(node.data.astId, node.id);
  }

  const refEdges = wfCollapsed ? [] : buildReferenceEdges(collectReferenceLinks(program), flowIdByAstId);

  const containerNode = {
    id: containerId,
    type: "appContainer",
    data: {
      astId: appNode.id,
      kind: "app",
      name: appNode.name || "MyApplication",
      renamable: true,
      declLabelY,
      workflowLabelY: workflows.length ? workflowLabelY : null,
      hasDeclarations: decls.length > 0,
      hasWorkflows: workflows.length > 0,
      declCount: decls.length,
      wfCount: workflows.length,
      declCollapsed,
      wfCollapsed,
    },
    position: { x: OUTER_PAD, y: OUTER_PAD },
    style: { width: containerW, height: containerH },
    width: containerW,
    height: containerH,
    selectable: true,
    draggable: false,
    zIndex: 0,
  };
  decorateNodeData(containerNode.data, appNode.id, options);

  for (const node of childNodes) {
    node.parentId = containerId;
    node.extent = "parent";
    node.draggable = false;
    node.zIndex = 1;
  }

  return {
    nodes: [containerNode, ...childNodes],
    edges: [...wfLayout.edges, ...refEdges],
  };
}
