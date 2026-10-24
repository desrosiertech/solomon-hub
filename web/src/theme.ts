export const THEMES = [
  { id: "light", label: "Light" },
  { id: "navy", label: "Navy" },
  { id: "dark", label: "Dark" },
] as const;

export type Theme = (typeof THEMES)[number]["id"];

const KEY = "solomon-theme";

export function readTheme(): Theme {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === "light" || saved === "navy" || saved === "dark") {
      return saved;
    }
  } catch {
    /* private mode */
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    /* private mode */
  }
}
