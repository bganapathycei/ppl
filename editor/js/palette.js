import { BLOCKS, PALETTE_GROUPS } from "./schema.js";
import { beginDrag, endDrag, selectKind, selectedKind } from "./dnd.js";

export function renderPalette(container) {
  container.innerHTML = PALETTE_GROUPS.map((group) => {
    const items = group.kinds
      .map((kind) => {
        const def = BLOCKS[kind];
        if (!def) return "";
        return `<button type="button" class="palette-item" draggable="true" data-kind="${kind}">
          <span class="swatch ${def.tone}"></span>${escapeHtml(def.keyword)}
        </button>`;
      })
      .join("");
    return `<h2>${escapeHtml(group.title)}</h2>${items}`;
  }).join("");

  container.addEventListener("click", (event) => {
    const item = event.target.closest("[data-kind]");
    if (!item) return;
    const kind = item.dataset.kind;
    selectKind(selectedKind === kind ? null : kind);
    container.querySelectorAll(".palette-item").forEach((el) => {
      el.classList.toggle("selected", el.dataset.kind === selectedKind);
    });
  });

  container.addEventListener("dragstart", (event) => {
    const item = event.target.closest("[data-kind]");
    if (!item) return;
    const kind = item.dataset.kind;
    beginDrag({ type: "kind", kind });
    event.dataTransfer.effectAllowed = "copy";
    event.dataTransfer.setData("text/plain", `kind:${kind}`);
  });
  container.addEventListener("dragend", () => {
    endDrag();
    document.querySelectorAll(".over").forEach((el) => el.classList.remove("over"));
  });
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
