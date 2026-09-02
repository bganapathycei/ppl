const STORAGE_KEY = "ppl-editor-theme";

export function getTheme() {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

function updateToggleButtons(theme) {
  const isLight = theme === "light";
  document.querySelectorAll("[data-theme-toggle]").forEach((el) => {
    el.setAttribute("aria-pressed", isLight ? "true" : "false");
    el.title = isLight ? "Switch to dark theme" : "Switch to light theme";
    const label = el.querySelector(".theme-toggle-label");
    if (label) label.textContent = isLight ? "Light" : "Dark";
    const icon = el.querySelector(".theme-toggle-icon");
    if (icon) icon.textContent = isLight ? "☀" : "☾";
  });
}

export function setTheme(theme) {
  const next = theme === "light" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try {
    localStorage.setItem(STORAGE_KEY, next);
  } catch {
    /* private mode */
  }
  updateToggleButtons(next);
  window.dispatchEvent(new CustomEvent("ppl-theme-change", { detail: { theme: next } }));
  return next;
}

export function toggleTheme() {
  return setTheme(getTheme() === "dark" ? "light" : "dark");
}

export function initTheme() {
  let stored = "dark";
  try {
    stored = localStorage.getItem(STORAGE_KEY) || "dark";
  } catch {
    /* private mode */
  }
  setTheme(stored);
}

export function bindThemeToggle(button) {
  if (!button) return;
  button.addEventListener("click", () => toggleTheme());
  updateToggleButtons(getTheme());
}
