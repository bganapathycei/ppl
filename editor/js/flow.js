// Interactive flow canvas: renders the auto-laid-out program as a pannable,
// zoomable flowchart. The document (AST) stays the source of truth; this module
// only reads it and reports intents (select / add) back to the host.

import { layoutProgram } from "./flow_layout.js";

const view = { tx: 24, ty: 20, scale: 1 };
let stageEl = null;
let lastLayout = null;

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function edgePath(e) {
  const midY = (e.y1 + e.y2) / 2;
  return `M ${e.x1} ${e.y1} C ${e.x1} ${midY}, ${e.x2} ${midY}, ${e.x2} ${e.y2}`;
}

function renderEdges(layout) {
  const paths = layout.edges
    .map((e) => {
      const cls = `flow-edge flow-edge-${e.kind}`;
      const marker = e.kind === "add" ? "" : ` marker-end="url(#flow-arrow)"`;
      return `<path class="${cls}" d="${edgePath(e)}"${marker}/>`;
    })
    .join("");
  const labels = layout.edges
    .filter((e) => e.label)
    .map(
      (e) =>
        `<text class="flow-edge-label" x="${e.labelX}" y="${e.labelY}" text-anchor="middle">${esc(e.label)}</text>`,
    )
    .join("");
  return `<svg class="flow-edges" width="${layout.width}" height="${layout.height}" viewBox="0 0 ${layout.width} ${layout.height}">
    <defs>
      <marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 1 L 9 5 L 0 9 z" fill="#5b6378"/>
      </marker>
    </defs>${paths}${labels}</svg>`;
}

function renderNode(item, selectedId) {
  if (item.kind === "merge") {
    return `<div class="flow-merge" style="left:${item.x}px;top:${item.y}px;width:${item.w}px;height:${item.h}px"></div>`;
  }
  if (item.kind === "add") {
    return `<button type="button" class="flow-add" data-add-owner="${item.addOwner}" data-add-slot="${item.addSlot}" data-add-index="${item.addIndex}" style="left:${item.x}px;top:${item.y}px;width:${item.w}px;height:${item.h}px">${esc(item.title)}</button>`;
  }
  const selected = item.selectable && item.id === selectedId ? " selected" : "";
  const clickable = item.selectable ? " selectable" : "";
  const lines = (item.lines || []).map((l) => `<span>${esc(l)}</span>`).join("");
  return `<div class="flow-node tone-${item.tone} role-${item.role}${selected}${clickable}" ${item.selectable ? `data-id="${item.id}"` : ""} style="left:${item.x}px;top:${item.y}px;width:${item.w}px;min-height:${item.h}px">
    <div class="flow-kw">${esc(item.keyword)}</div>
    <div class="flow-title">${esc(item.title)}</div>
    ${lines ? `<div class="flow-lines">${lines}</div>` : ""}
  </div>`;
}

function applyTransform() {
  if (stageEl) stageEl.style.transform = `translate(${view.tx}px, ${view.ty}px) scale(${view.scale})`;
}

export function renderFlow(container, program, selectedId) {
  const maxWidth = Math.max(700, container.clientWidth - 80);
  const layout = layoutProgram(program, { maxWidth });
  lastLayout = layout;
  const nodes = layout.items.map((item) => renderNode(item, selectedId)).join("");
  container.innerHTML = `<div class="flow-stage" style="width:${layout.width}px;height:${layout.height}px">${renderEdges(layout)}${nodes}</div>`;
  stageEl = container.querySelector(".flow-stage");
  applyTransform();
}

export function fitFlow(container) {
  if (!lastLayout) return;
  const availW = container.clientWidth - 40;
  const availH = container.clientHeight - 40;
  const scale = Math.min(1, availW / lastLayout.width, availH / lastLayout.height);
  view.scale = Math.max(0.2, scale || 1);
  view.tx = 24;
  view.ty = 20;
  applyTransform();
}

export function zoomFlow(container, factor) {
  view.scale = Math.min(2.2, Math.max(0.2, view.scale * factor));
  applyTransform();
}

export function bindFlow(container, getProgram, handlers) {
  container.addEventListener("click", (event) => {
    const add = event.target.closest(".flow-add");
    if (add) {
      handlers.onAdd(add.dataset.addOwner, add.dataset.addSlot, Number(add.dataset.addIndex));
      return;
    }
    const node = event.target.closest(".flow-node.selectable");
    if (node) {
      handlers.onSelect(node.dataset.id);
      return;
    }
    if (!event.target.closest(".flow-node")) handlers.onSelect(null);
  });

  // Wheel zoom toward the pointer.
  container.addEventListener(
    "wheel",
    (event) => {
      if (!event.ctrlKey && Math.abs(event.deltaY) < 1) return;
      event.preventDefault();
      const rect = container.getBoundingClientRect();
      const px = event.clientX - rect.left;
      const py = event.clientY - rect.top;
      const prev = view.scale;
      const next = Math.min(2.2, Math.max(0.2, prev * (event.deltaY < 0 ? 1.1 : 0.9)));
      const k = next / prev;
      view.tx = px - (px - view.tx) * k;
      view.ty = py - (py - view.ty) * k;
      view.scale = next;
      applyTransform();
    },
    { passive: false },
  );

  // Drag background to pan.
  let panning = null;
  container.addEventListener("pointerdown", (event) => {
    if (event.target.closest(".flow-node, .flow-add")) return;
    panning = { x: event.clientX, y: event.clientY, tx: view.tx, ty: view.ty };
    container.classList.add("panning");
    container.setPointerCapture(event.pointerId);
  });
  container.addEventListener("pointermove", (event) => {
    if (!panning) return;
    view.tx = panning.tx + (event.clientX - panning.x);
    view.ty = panning.ty + (event.clientY - panning.y);
    applyTransform();
  });
  const endPan = () => {
    panning = null;
    container.classList.remove("panning");
  };
  container.addEventListener("pointerup", endPan);
  container.addEventListener("pointercancel", endPan);
}
