import { useEffect, useState } from "react";
import { getTheme, initTheme } from "../../js/theme.js";

export function useEditorTheme() {
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    initTheme();
    setTheme(getTheme());
    const onTheme = () => setTheme(getTheme());
    const observer = new MutationObserver(onTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    window.addEventListener("ppl-theme-change", onTheme);
    return () => {
      observer.disconnect();
      window.removeEventListener("ppl-theme-change", onTheme);
    };
  }, []);

  return theme;
}

export function themeColor(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
