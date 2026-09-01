// Convert a PPL document (AST) into React Flow nodes/edges, laid out with
// dagre. The AST stays the source of truth (shared parse/codegen keep `.ppl`
// round-tripping); this module derives a control-flow graph:
//   - workflow steps chain top-to-bottom
//   - IF / PARALLEL fan out into labeled branches that merge (RETURN paths
//     terminate and do not merge onward)
//   - declarations and agents are placed as reference cards in a left column
import dagre from "@dagrejs/dagre";
import { summarize, tone } from "../../js/flow_layout.js";
import { BLOCKS } from "../../js/schema.js";

const NODE_W = 224;

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
    },
    position: { x: 0, y: 0 },
    width: NODE_W,
    height: nodeHeight(lines),
  };
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

// Emit a vertical sequence. Returns entry id, open exits, and collected graph.
function emitSequence(steps) {
  const nodes = [];
  const edges = [];
  let entry = null;
  let openEnds = [];
  for (const step of steps || []) {
    const r = emitStep(step);
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

function emitBranches(headerNode, branches) {
  const nodes = [headerNode];
  const edges = [];
  const exits = [];
  for (const branch of branches) {
    const seq = emitSequence(branch.steps);
    nodes.push(...seq.nodes);
    edges.push(...seq.edges);
    edges.push(edge(headerNode.id, seq.entry, branch.label, "branch"));
    exits.push(...seq.exits);
  }
  return { nodes, edges, entry: headerNode.id, exits };
}

function emitStep(node) {
  if (node.kind === "if") {
    const branches = [{ label: "then", steps: node.children }];
    for (const b of node.elseIf || []) branches.push({ label: `else if ${conditionLabel(b)}`, steps: b.children });
    branches.push({ label: "else", steps: node.elseChildren });
    return emitBranches(makeNode(node, "step"), branches);
  }
  if (node.kind === "parallel") {
    const kids = node.children || [];
    const branches = kids.length
      ? kids.map((child, i) => ({ label: `branch ${i + 1}`, steps: [child] }))
      : [{ label: "branch", steps: [] }];
    return emitBranches(makeNode(node, "step"), branches);
  }
  const single = makeNode(node, "step");
  // RETURN terminates the path (no open exit).
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
  return { minX, maxX, minY, maxY };
}

export function buildFlow(program) {
  ghostSeq = 0;
  const children = program.children || [];
  const decls = children.filter((c) => c.kind !== "workflow");
  const workflows = children.filter((c) => c.kind === "workflow");

  const cfNodes = [];
  const cfEdges = [];
  for (const wf of workflows) {
    const header = makeNode(wf, "workflow-title");
    const body = emitSequence(wf.children);
    cfNodes.push(header, ...body.nodes);
    cfEdges.push(edge(header.id, body.entry), ...body.edges);
  }

  let bounds = { minX: 0, maxX: NODE_W, minY: 0, maxY: 0 };
  if (cfNodes.length) bounds = layoutControlFlow(cfNodes, cfEdges);

  // Declaration / agent cards in a left column.
  const colX = bounds.minX - NODE_W - 70;
  let y = bounds.minY;
  const declNodes = decls.map((node) => {
    const card = makeNode(node, node.kind === "agent" ? "agent" : "resource");
    card.position = { x: cfNodes.length ? colX : 20, y };
    y += card.height + 26;
    return card;
  });

  return { nodes: [...declNodes, ...cfNodes], edges: cfEdges };
}
