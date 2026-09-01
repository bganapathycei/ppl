// Properties inspector for the flow canvas.
//
// Renders a schema-driven form for the selected AST node (fields from
// schema.js plus inline editors for simple list slots) and writes edits back
// into the document via model.js. Structure for complex slots (workflow steps,
// agent bodies) is still added on the canvas or in the Blocks view.

import { BLOCKS, TYPES, OPERATORS } from "./schema.js";
import { createNode, getNode, getSlot, insertNode, removeNode, setProp } from "./model.js";

const SIMPLE_KINDS = new Set([
  "field",
  "category",
  "option",
  "source",
  "rule",
  "memory_clause",
  "consider",
  "arg",
]);

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function control(node, field) {
  const value = node[field.prop];
  const id = node.id;
  const prop = field.prop;
  if (field.kind === "textarea") {
    return `<textarea data-id="${id}" data-prop="${prop}" rows="3" placeholder="${esc(field.placeholder || "")}">${esc(value ?? "")}</textarea>`;
  }
  if (field.kind === "type") {
    const opts = TYPES.map((t) => `<option value="${esc(t)}" ${String(value ?? "") === t ? "selected" : ""}>${t || "—"}</option>`).join("");
    return `<select data-id="${id}" data-prop="${prop}">${opts}</select>`;
  }
  if (field.kind === "operator") {
    const opts = OPERATORS.map((o) => `<option value="${o}" ${value === o ? "selected" : ""}>${o}</option>`).join("");
    return `<select data-id="${id}" data-prop="${prop}">${opts}</select>`;
  }
  if (field.kind === "check") {
    return `<label class="insp-check"><input type="checkbox" data-id="${id}" data-prop="${prop}" ${value ? "checked" : ""}> ${esc(field.label || prop)}</label>`;
  }
  return `<input data-id="${id}" data-prop="${prop}" value="${esc(value ?? "")}" placeholder="${esc(field.placeholder || "")}">`;
}

function fieldRow(node, field) {
  if (field.kind === "check") return `<div class="insp-row">${control(node, field)}</div>`;
  const label = field.prop.replace(/_/g, " ");
  return `<div class="insp-row"><label class="insp-label">${esc(label)}</label>${control(node, field)}</div>`;
}

function inlineSlot(node, spec) {
  const list = getSlot(node, spec.name) || [];
  const childKind = spec.accept[0];
  const childDef = BLOCKS[childKind] || {};
  let html = `<div class="insp-slot"><div class="insp-slot-head"><span>${esc(spec.label || spec.name)}</span>`;
  html += `<button type="button" class="insp-add" data-additem="${node.id}" data-slot="${spec.name}" data-kind="${childKind}">+ ${esc(childDef.keyword || childKind)}</button></div>`;
  if (!list.length) html += `<p class="insp-empty">none</p>`;
  for (const item of list) {
    html += `<div class="insp-item">`;
    for (const field of childDef.fields || []) html += control(item, field);
    html += `<button type="button" class="insp-del" data-delitem="${item.id}" title="Remove">✕</button>`;
    html += `</div>`;
  }
  html += `</div>`;
  return html;
}

export function renderInspector(container, program, selectedId, handlers) {
  const node = selectedId ? getNode(program, selectedId) : null;
  if (!node) {
    container.innerHTML = `<p class="insp-hint">Select a node on the canvas to edit its properties.</p>`;
    return;
  }
  const def = BLOCKS[node.kind] || {};
  let html = `<div class="insp-title"><span class="insp-kw tone-${def.tone || "det"}">${esc(def.keyword || node.kind)}</span>`;
  if (node.kind !== "app" && node.kind !== "program") {
    html += `<button type="button" class="insp-remove" data-remove="${node.id}">Delete</button>`;
  }
  html += `</div>`;

  for (const field of def.fields || []) html += fieldRow(node, field);

  for (const spec of def.slots || []) {
    if ((spec.accept || []).every((k) => SIMPLE_KINDS.has(k))) html += inlineSlot(node, spec);
  }

  const complex = (def.slots || []).filter((spec) => !(spec.accept || []).every((k) => SIMPLE_KINDS.has(k)));
  if (complex.length) {
    html += `<p class="insp-hint">Add ${complex
      .map((s) => (s.label || s.name).toLowerCase())
      .join(", ")} from the canvas “+” or the Blocks view.</p>`;
  }

  container.innerHTML = html;
}

export function bindInspector(container, getProgram, getSelectedId, handlers) {
  const editEvent = (event) => {
    const target = event.target;
    const id = target.dataset?.id;
    const prop = target.dataset?.prop;
    if (!id || !prop) return;
    const node = getNode(getProgram(), id);
    if (!node) return;
    const value = target.type === "checkbox" ? target.checked : target.value;
    setProp(node, prop, value);
    handlers.onEdit();
  };
  container.addEventListener("input", editEvent);
  container.addEventListener("change", editEvent);

  container.addEventListener("click", (event) => {
    const program = getProgram();
    const remove = event.target.closest("[data-remove]");
    if (remove) {
      removeNode(program, remove.dataset.remove);
      handlers.onStructure(null);
      return;
    }
    const del = event.target.closest("[data-delitem]");
    if (del) {
      removeNode(program, del.dataset.delitem);
      handlers.onStructure(getSelectedId());
      return;
    }
    const add = event.target.closest("[data-additem]");
    if (add) {
      const parent = getNode(program, add.dataset.additem);
      if (!parent) return;
      const list = getSlot(parent, add.dataset.slot) || [];
      insertNode(parent, add.dataset.slot, list.length, createNode(add.dataset.kind));
      handlers.onStructure(getSelectedId());
    }
  });
}
