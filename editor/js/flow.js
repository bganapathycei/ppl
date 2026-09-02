// Interactive flow canvas: renders the auto-laid-out program as a pannable,
// zoomable flowchart. The document (AST) stays the source of truth; this module
// only reads it and reports intents (select / add / drop) back to the host.

import { layoutProgram } from "./flow_layout.js";
import { drag, endDrag } from "./dnd.js";

const view = { tx: 24, ty: 20, scale: 1 };
let stageEl = null;
let lastLayout = null;
let flowHandlers = null;
let flowOptions = {};

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

function renderContainer(container, selectedId) {
  const selected = container.selectable && container.id === selectedId ? " selected" : "";
  const selectable = container.selectable ? " selectable" : "";
  const declToggle = container.hasDeclarations
    ? `<button type="button" class="flow-container-section-toggle${container.declCollapsed ? " collapsed" : ""}" data-toggle="decl" style="top:${container.declLabelY - container.y}px">${container.declCollapsed ? "▸" : "▾"} Declarations${container.declCount ? ` (${container.declCount})` : ""}</button>`
    : "";
  const workflowToggle =
    container.hasWorkflows && container.workflowLabelY != null
      ? `<button type="button" class="flow-container-section-toggle${container.wfCollapsed ? " collapsed" : ""}" data-toggle="wf" style="top:${container.workflowLabelY - container.y}px">${container.wfCollapsed ? "▸" : "▾"} Workflows${container.wfCount ? ` (${container.wfCount})` : ""}</button>`
      : "";
  const nameCls = container.renamable ? " flow-container-name flow-renamable" : " flow-container-name";
  return `<div class="flow-container${selected}${selectable}" ${container.selectable ? `data-id="${container.id}"` : ""} style="left:${container.x}px;top:${container.y}px;width:${container.w}px;height:${container.h}px">
    <div class="flow-container-header">
      <span class="flow-container-kw">APP</span>
      <span class="${nameCls.trim()}" ${container.renamable ? `data-rename-id="${container.id}"` : ""}>${esc(container.appName)}</span>
    </div>${declToggle}${workflowToggle}
  </div>`;
}

function renderEdges(layout) {
  const paths = layout.edges
    .map((e) => {
      const cls = `flow-edge flow-edge-${e.kind}${e.refActive ? " flow-edge-ref-active" : ""}`;
      const marker = e.kind === "add" || e.kind === "ref" ? "" : ` marker-end="url(#flow-arrow)"`;
      return `<path class="${cls}" d="${edgePath(e)}"${marker}/>`;
    })
    .join("");
  const labels = layout.edges
    .filter((e) => e.label)
    .map((e) => {
      const text = e.label.length > 22 ? e.label.slice(0, 21) + "…" : e.label;
      const w = text.length * 6 + 10;
      return `<g class="flow-label-g">
        <rect class="flow-edge-label-bg" x="${e.labelX - w / 2}" y="${e.labelY - 9}" width="${w}" height="15" rx="4"/>
        <text class="flow-edge-label" x="${e.labelX}" y="${e.labelY + 2}" text-anchor="middle">${esc(text)}</text>
      </g>`;
    })
    .join("");
  return `<svg class="flow-edges" width="${layout.width}" height="${layout.height}" viewBox="0 0 ${layout.width} ${layout.height}">
    <defs>
      <marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 1 L 9 5 L 0 9 z" class="flow-arrow-head"/>
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
  const issueCls = item.issueLevel ? ` has-issue issue-${item.issueLevel}` : "";
  const traceCls = item.traceStatus ? ` trace-${item.traceStatus}` : "";
  const refCls = item.refHighlight ? " ref-highlight" : "";
  const renameCls = item.renamable ? " flow-renamable" : "";
  const lines = (item.lines || []).map((l) => `<span>${esc(l)}</span>`).join("");
  const badge = item.issueLevel
    ? `<span class="flow-issue flow-issue-${item.issueLevel}" title="${esc(item.issueTip || "")}">!</span>`
    : "";
  return `<div class="flow-node tone-${item.tone} role-${item.role}${selected}${clickable}${issueCls}${traceCls}${refCls}" ${item.selectable ? `data-id="${item.id}"` : ""} style="left:${item.x}px;top:${item.y}px;width:${item.w}px;min-height:${item.h}px">
    ${badge}
    <div class="flow-kw">${esc(item.keyword)}</div>
    <div class="flow-title${renameCls}" ${item.renamable ? `data-rename-id="${item.id}"` : ""}>${esc(item.title)}</div>
    ${lines ? `<div class="flow-lines">${lines}</div>` : ""}
  </div>`;
}

function applyTransform() {
  if (stageEl) stageEl.style.transform = `translate(${view.tx}px, ${view.ty}px) scale(${view.scale})`;
}

export function renderFlow(container, program, selectedId, options = {}) {
  flowOptions = options;
  const maxWidth = Math.max(700, container.clientWidth - 80);
  const layout = layoutProgram(program, { maxWidth, ...options });
  lastLayout = layout;
  const containerHtml = layout.container ? renderContainer(layout.container, selectedId) : "";
  const nodes = layout.items.map((item) => renderNode(item, selectedId)).join("");
  container.innerHTML = `<div class="flow-stage" style="width:${layout.width}px;height:${layout.height}px">${renderEdges(layout)}${containerHtml}<div class="flow-nodes">${nodes}</div></div>`;
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

export function applyFlowDecorations(root, { hoverAstId, refLinked } = {}) {
  if (!root) return;
  root.querySelectorAll(".flow-node.selectable").forEach((el) => {
    const id = el.dataset.id;
    el.classList.toggle("ref-highlight", Boolean(id && (refLinked?.has(id) || id === hoverAstId)));
  });
}

function startInlineRename(target) {
  const id = target.dataset.renameId;
  if (!id || target.querySelector("input")) return;
  const current = target.textContent;
  const input = document.createElement("input");
  input.className = "flow-rename-input";
  input.value = current;
  target.textContent = "";
  target.appendChild(input);
  input.focus();
  input.select();
  const commit = () => {
    const value = input.value.trim() || current;
    flowHandlers?.onRename?.(id, value);
  };
  input.addEventListener("blur", commit);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") input.blur();
    if (e.key === "Escape") {
      target.textContent = current;
      input.remove();
    }
    e.stopPropagation();
  });
  input.addEventListener("dblclick", (e) => e.stopPropagation());
}

function clearDropHighlights(root) {
  root.querySelectorAll(".flow-drop-over").forEach((el) => el.classList.remove("flow-drop-over"));
}

function dropTargetFromEvent(event) {
  const add = event.target.closest(".flow-add");
  if (add) {
    return {
      ownerId: add.dataset.addOwner,
      slot: add.dataset.addSlot || "children",
      index: Number(add.dataset.addIndex),
      el: add,
    };
  }
  const workflowTitle = event.target.closest(".flow-node.role-workflow-title");
  if (workflowTitle?.dataset.id) {
    return { ownerId: workflowTitle.dataset.id, slot: "children", index: Infinity, el: workflowTitle };
  }
  return null;
}

export function bindFlow(container, getProgram, handlers) {
  flowHandlers = handlers;

  container.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-toggle]");
    if (toggle) {
      if (toggle.dataset.toggle === "decl") handlers.onToggleDecl?.();
      if (toggle.dataset.toggle === "wf") handlers.onToggleWf?.();
      return;
    }
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
    const containerNode = event.target.closest(".flow-container.selectable");
    if (containerNode) {
      handlers.onSelect(containerNode.dataset.id);
      return;
    }
    if (!event.target.closest(".flow-node, .flow-add, .flow-container")) handlers.onSelect(null);
  });

  container.addEventListener("dragover", (event) => {
    const target = dropTargetFromEvent(event);
    clearDropHighlights(container);
    if (!target) return;
    const hasKind =
      (drag?.type === "kind" && drag.kind) ||
      event.dataTransfer?.types?.includes("application/x-ppl-kind") ||
      event.dataTransfer?.types?.includes("text/plain");
    if (!hasKind) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    target.el.classList.add("flow-drop-over");
  });

  container.addEventListener("dragleave", (event) => {
    if (!container.contains(event.relatedTarget)) clearDropHighlights(container);
  });

  container.addEventListener("drop", (event) => {
    const target = dropTargetFromEvent(event);
    clearDropHighlights(container);
    if (!target) return;
    event.preventDefault();
    const kind =
      (drag?.type === "kind" && drag.kind) ||
      event.dataTransfer.getData("application/x-ppl-kind") ||
      (event.dataTransfer.getData("text/plain") || "").replace(/^kind:/, "");
    endDrag();
    if (!kind) return;
    handlers.onDrop?.(kind, target.ownerId, target.slot, target.index);
  });

  container.addEventListener("dblclick", (event) => {
    const rename = event.target.closest(".flow-renamable");
    if (rename) {
      event.preventDefault();
      event.stopPropagation();
      startInlineRename(rename);
    }
  });

  container.addEventListener(
    "mouseenter",
    (event) => {
      const node = event.target.closest(".flow-node.selectable");
      if (node?.dataset.id) handlers.onHover?.(node.dataset.id);
    },
    true,
  );

  container.addEventListener(
    "mouseleave",
    (event) => {
      const node = event.target.closest(".flow-node.selectable");
      if (node?.dataset.id) handlers.onHoverEnd?.();
    },
    true,
  );

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

  let panning = null;
  container.addEventListener("pointerdown", (event) => {
    if (event.target.closest(".flow-node, .flow-add, .flow-container, .flow-rename-input")) return;
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
