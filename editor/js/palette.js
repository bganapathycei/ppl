import { BLOCKS, PALETTE_GROUPS } from "./schema.js";
import { beginDrag, endDrag, selectKind, selectedKind } from "./dnd.js";

export function renderPalette(container) {
  container.innerHTML = `<p class="palette-hint">Select a block, then click “+ step” on the canvas — or drag onto “+ step”. Double-click a block to insert.</p>${PALETTE_GROUPS.map((group) => {
    const items = group.kinds
      .map((kind) => {
        const def = BLOCKS[kind];
        if (!def) return "";
        return `<button type="button" class="palette-item" draggable="true" data-kind="${kind}" title="${escapeHtml(def.keyword)}">
          <span class="swatch ${def.tone}"></span>${escapeHtml(def.keyword)}
        </button>`;
      })
      .join("");
    return `<h2>${escapeHtml(group.title)}</h2>${items}`;
  }).join("")}`;

  // Replacing innerHTML removes old listeners; bind once per mount via property flag.
  if (container.dataset.paletteBound === "1") return;
  container.dataset.paletteBound = "1";

  container.addEventListener("click", (event) => {
    const item = event.target.closest("[data-kind]");
    if (!item) return;
    const kind = item.dataset.kind;
    // Second click on the same selected block = insert (React editor UX).
    if (selectedKind === kind) {
      container.dispatchEvent(new CustomEvent("ppl-palette-insert", { detail: { kind }, bubbles: true }));
      return;
    }
    selectKind(kind);
    syncSelected(container);
  });

  container.addEventListener("dblclick", (event) => {
    const item = event.target.closest("[data-kind]");
    if (!item) return;
    event.preventDefault();
    const kind = item.dataset.kind;
    selectKind(kind);
    syncSelected(container);
    container.dispatchEvent(new CustomEvent("ppl-palette-insert", { detail: { kind }, bubbles: true }));
  });

  container.addEventListener("dragstart", (event) => {
    const item = event.target.closest("[data-kind]");
    if (!item) return;
    const kind = item.dataset.kind;
    selectKind(kind);
    syncSelected(container);
    beginDrag({ type: "kind", kind });
    event.dataTransfer.effectAllowed = "copy";
    event.dataTransfer.setData("text/plain", `kind:${kind}`);
    event.dataTransfer.setData("application/x-ppl-kind", kind);
  });
  container.addEventListener("dragend", () => {
    endDrag();
    document.querySelectorAll(".over, .flow-drop-over").forEach((el) => {
      el.classList.remove("over");
      el.classList.remove("flow-drop-over");
    });
  });
}

export function syncPaletteSelection(container) {
  syncSelected(container);
}

function syncSelected(container) {
  container.querySelectorAll(".palette-item").forEach((el) => {
    el.classList.toggle("selected", el.dataset.kind === selectedKind);
  });
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
