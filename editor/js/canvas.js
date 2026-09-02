import { BLOCKS, TYPES, OPERATORS, accepts } from "./schema.js";
import {
  contains,
  createNode,
  getNode,
  getSlot,
  insertNode,
  moveNode,
  removeNode,
  setProp,
} from "./model.js";
import { beginDrag, clearSelectedKind, drag, endDrag, selectedKind } from "./dnd.js";

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fieldControl(node, field) {
  const value = node[field.prop];
  const cls = field.grow ? "grow" : "";
  if (field.kind === "textarea") {
    return `<textarea data-id="${node.id}" data-prop="${field.prop}" class="${cls}" placeholder="${escapeHtml(field.placeholder || "")}">${escapeHtml(value ?? "")}</textarea>`;
  }
  if (field.kind === "type") {
    const options = TYPES.map(
      (item) =>
        `<option value="${escapeHtml(item)}" ${String(value ?? "") === item ? "selected" : ""}>${item || "—"}</option>`,
    ).join("");
    return `<select data-id="${node.id}" data-prop="${field.prop}">${options}</select>`;
  }
  if (field.kind === "operator") {
    const options = OPERATORS.map(
      (item) => `<option value="${item}" ${value === item ? "selected" : ""}>${item}</option>`,
    ).join("");
    return `<select data-id="${node.id}" data-prop="${field.prop}">${options}</select>`;
  }
  if (field.kind === "check") {
    return `<label><input type="checkbox" data-id="${node.id}" data-prop="${field.prop}" ${value ? "checked" : ""}> ${escapeHtml(field.label || field.prop)}</label>`;
  }
  return `<input data-id="${node.id}" data-prop="${field.prop}" class="${cls}" value="${escapeHtml(value ?? "")}" placeholder="${escapeHtml(field.placeholder || "")}">`;
}

function renderSlot(parent, slot, label) {
  const spec = (BLOCKS[parent.kind]?.slots || []).find((item) => item.name === slot);
  const list = getSlot(parent, slot) || [];
  const accept = (spec?.accept || []).join(",");
  let html = `<div class="slot" data-drop="1" data-parent="${parent.id}" data-slot="${slot}" data-index="${list.length}" data-accept="${accept}">`;
  if (label) html += `<div class="slot-label">${escapeHtml(label)}</div>`;
  list.forEach((child, index) => {
    html += `<div class="drop-gap" data-drop="1" data-parent="${parent.id}" data-slot="${slot}" data-index="${index}"></div>`;
    html += renderBlock(child);
  });
  html += `<div class="drop-gap" data-drop="1" data-parent="${parent.id}" data-slot="${slot}" data-index="${list.length}"></div>`;
  html += "</div>";
  return html;
}

function renderBlock(node) {
  const def = BLOCKS[node.kind];
  if (!def) return "";
  let html = `<div class="block tone-${def.tone}" data-id="${node.id}">`;
  html += `<div class="block-head" draggable="true" data-drag-id="${node.id}">`;
  html += `<span class="kw">${escapeHtml(def.keyword)}</span>`;
  for (const field of def.fields || []) html += fieldControl(node, field);
  html += `<button type="button" class="icon-btn" data-delete="${node.id}" title="Delete">✕</button>`;
  html += "</div>";
  for (const spec of def.slots || []) html += renderSlot(node, spec.name, spec.label);
  html += "</div>";
  return html;
}

function dragKind(program) {
  if (!drag) return null;
  if (drag.type === "kind") return drag.kind;
  return getNode(program, drag.id)?.kind || null;
}

function canDropOn(program, zone) {
  const kind = dragKind(program);
  const parent = getNode(program, zone.dataset.parent);
  if (!kind || !parent) return false;
  if (drag?.type === "move") {
    const moving = getNode(program, drag.id);
    if (!moving) return false;
    if (moving.id === parent.id || contains(moving, parent.id)) return false;
  }
  return accepts(parent, zone.dataset.slot, kind, {
    movingId: drag?.type === "move" ? drag.id : null,
  });
}

function applyDrop(program, zone) {
  const parent = getNode(program, zone.dataset.parent);
  const slot = zone.dataset.slot;
  const index = Number(zone.dataset.index);
  if (!parent || !drag) return false;
  if (drag.type === "kind") {
    return insertNode(parent, slot, index, createNode(drag.kind));
  }
  if (drag.type === "move") {
    return moveNode(program, drag.id, parent.id, slot, index);
  }
  return false;
}

export function renderCanvas(container, program) {
  const children = program.children || [];
  const accept = (BLOCKS.program?.slots?.[0]?.accept || []).join(",");
  let html = `<div class="slot" data-drop="1" data-parent="${program.id}" data-slot="children" data-index="${children.length}" data-accept="${accept}">`;
  html += `<div class="slot-label">Program</div>`;
  html += `<div class="program-section-label">Declarations</div>`;

  let index = 0;
  let sawWorkflow = false;
  for (const child of children) {
    if (child.kind === "workflow" && !sawWorkflow) {
      html += `<div class="program-section-label">Workflows</div>`;
      sawWorkflow = true;
    }
    html += `<div class="drop-gap" data-drop="1" data-parent="${program.id}" data-slot="children" data-index="${index}" data-accept="${accept}"></div>`;
    html += renderBlock(child);
    index += 1;
  }
  html += `<div class="drop-gap" data-drop="1" data-parent="${program.id}" data-slot="children" data-index="${index}" data-accept="${accept}"></div>`;
  html += "</div>";
  container.innerHTML = html;
}

export function bindCanvas(container, getProgram, handlers) {
  container.addEventListener("input", (event) => {
    const program = getProgram();
    const target = event.target;
    const id = target.dataset?.id;
    const prop = target.dataset?.prop;
    if (!id || !prop || target.type === "checkbox") return;
    const node = getNode(program, id);
    if (!node) return;
    setProp(node, prop, target.value);
    handlers.onEdit();
  });

  container.addEventListener("change", (event) => {
    const program = getProgram();
    const target = event.target;
    const id = target.dataset?.id;
    const prop = target.dataset?.prop;
    if (!id || !prop) return;
    const node = getNode(program, id);
    if (!node) return;
    setProp(node, prop, target.type === "checkbox" ? target.checked : target.value);
    handlers.onEdit();
  });

  container.addEventListener("click", (event) => {
    const program = getProgram();
    const button = event.target.closest("[data-delete]");
    if (button) {
      event.preventDefault();
      removeNode(program, button.dataset.delete);
      handlers.onStructure();
      return;
    }
    if (!selectedKind || event.target.closest("input, select, textarea, button, .block-head")) return;
    const zone = event.target.closest("[data-drop]");
    if (!zone) return;
    beginDrag({ type: "kind", kind: selectedKind });
    const ok = canDropOn(program, zone);
    if (ok) applyDrop(program, zone);
    endDrag();
    if (ok) {
      clearSelectedKind();
      document.querySelectorAll(".palette-item.selected").forEach((el) => el.classList.remove("selected"));
      handlers.onStructure();
    }
  });

  container.addEventListener("dragstart", (event) => {
    const handle = event.target.closest("[data-drag-id]");
    if (!handle) return;
    beginDrag({ type: "move", id: handle.dataset.dragId });
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", `move:${handle.dataset.dragId}`);
  });

  container.addEventListener("dragend", () => {
    endDrag();
    container.querySelectorAll(".over").forEach((el) => el.classList.remove("over"));
  });

  container.addEventListener("dragover", (event) => {
    const program = getProgram();
    const zone = event.target.closest("[data-drop]");
    container.querySelectorAll(".over").forEach((el) => el.classList.remove("over"));
    if (!zone || !canDropOn(program, zone)) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = drag?.type === "kind" ? "copy" : "move";
    zone.classList.add("over");
  });

  container.addEventListener("drop", (event) => {
    const program = getProgram();
    const zone = event.target.closest("[data-drop]");
    if (!zone || !canDropOn(program, zone)) return;
    event.preventDefault();
    applyDrop(program, zone);
    endDrag();
    handlers.onStructure();
  });
}
