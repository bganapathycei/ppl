import { useEffect, useState } from "react";
import { getTheme, toggleTheme, initTheme } from "../../js/theme.js";

export default function ThemeToggle() {
  const [theme, setThemeState] = useState("dark");

  useEffect(() => {
    initTheme();
    setThemeState(getTheme());
  }, []);

  const isLight = theme === "light";

  return (
    <button
      type="button"
      className="theme-toggle"
      data-theme-toggle
      aria-pressed={isLight}
      title={isLight ? "Switch to dark theme" : "Switch to light theme"}
      onClick={() => setThemeState(toggleTheme())}
    >
      <span className="theme-toggle-icon" aria-hidden="true">
        {isLight ? "☀" : "☾"}
      </span>
      <span className="theme-toggle-label">{isLight ? "Light" : "Dark"}</span>
    </button>
  );
}
