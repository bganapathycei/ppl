export let drag = null;
export let selectedKind = null;

export function beginDrag(info) {
  drag = info;
}

export function endDrag() {
  drag = null;
}

export function selectKind(kind) {
  selectedKind = kind;
}

export function clearSelectedKind() {
  selectedKind = null;
}
