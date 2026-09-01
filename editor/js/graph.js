const CLASS_OF = {
  HUMAN_APPROVAL: "h",
  CLASSIFY: "c",
  EXTRACT: "c",
  REASON: "c",
};

function xml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function tone(operation) {
  return CLASS_OF[operation] || "d";
}

function layout(nodes) {
  const byId = Object.fromEntries(nodes.map((node) => [node.id, node]));
  const layer = {};
  const visiting = new Set();

  function depth(id) {
    if (layer[id] != null) return layer[id];
    if (visiting.has(id)) return 0;
    visiting.add(id);
    const node = byId[id];
    const deps = (node?.dependencies || []).filter((dep) => byId[dep]);
    layer[id] = deps.length ? Math.max(...deps.map(depth)) + 1 : 0;
    visiting.delete(id);
    return layer[id];
  }

  for (const node of nodes) depth(node.id);
  const columns = [];
  for (const node of nodes) {
    const col = layer[node.id] || 0;
    if (!columns[col]) columns[col] = [];
    columns[col].push(node);
  }
  const width = 148;
  const height = 36;
  const xGap = 56;
  const yGap = 16;
  const pos = {};
  columns.forEach((col, x) => {
    col.forEach((node, y) => {
      pos[node.id] = {
        x: 16 + x * (width + xGap),
        y: 16 + y * (height + yGap),
        width,
        height,
      };
    });
  });
  const maxX = Math.max(320, ...Object.values(pos).map((p) => p.x + p.width + 16));
  const maxY = Math.max(120, ...Object.values(pos).map((p) => p.y + p.height + 16));
  return { pos, maxX, maxY, width, height };
}

export function renderGraph(container, graph, error, meta = "") {
  const nodes = graph?.nodes || [];
  if (error && !nodes.length) {
    container.innerHTML = `<p class="graph-error">${xml(error)}</p>`;
    return;
  }
  if (!nodes.length) {
    container.innerHTML = `<p class="graph-meta">${xml(meta || "No graph nodes yet.")}</p>`;
    return;
  }
  const { pos, maxX, maxY } = layout(nodes);
  const edges = [];
  for (const node of nodes) {
    for (const dep of node.dependencies || []) {
      if (!pos[dep] || !pos[node.id]) continue;
      const a = pos[dep];
      const b = pos[node.id];
      const x1 = a.x + a.width;
      const y1 = a.y + a.height / 2;
      const x2 = b.x;
      const y2 = b.y + b.height / 2;
      const mid = (x1 + x2) / 2;
      edges.push(
        `<path d="M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}" fill="none" stroke="#5b6378" stroke-width="1.4"/>`,
      );
    }
  }
  const boxes = nodes
    .map((node) => {
      const p = pos[node.id];
      const label = `${node.operation} ${node.name && node.name !== node.operation ? node.name : ""}`.trim();
      return `<g>
        <rect class="node-${tone(node.operation)}" x="${p.x}" y="${p.y}" width="${p.width}" height="${p.height}" rx="7"/>
        <text x="${p.x + 10}" y="${p.y + 22}" fill="#e7e9f0" font-size="11" font-family="Segoe UI, sans-serif">${xml(label.slice(0, 22))}</text>
      </g>`;
    })
    .join("");
  const banner = error ? `<p class="graph-error">${xml(error)}</p>` : "";
  container.innerHTML = `${banner}<svg xmlns="http://www.w3.org/2000/svg" width="${maxX}" height="${maxY}" viewBox="0 0 ${maxX} ${maxY}">${edges.join("")}${boxes}</svg>`;
}
