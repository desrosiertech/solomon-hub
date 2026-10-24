import { useState } from "react";
import { applyTheme, readTheme, THEMES, type Theme } from "../theme";

export function ThemeSwitch() {
  const [theme, setTheme] = useState<Theme>(() => readTheme());

  function choose(next: Theme) {
    applyTheme(next);
    setTheme(next);
  }

  return (
    <div className="flex rounded-full border border-line p-1" role="group" aria-label="Theme">
      {THEMES.map((item) => (
        <button
          key={item.id}
          type="button"
          aria-pressed={theme === item.id}
          onClick={() => choose(item.id)}
          className={`rounded-full px-3 py-1 text-sm ${
            theme === item.id ? "bg-accent text-on-accent" : "text-muted"
          }`}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
