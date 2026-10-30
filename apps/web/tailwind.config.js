/** @type {import('tailwindcss').Config} */

// Most of our palette lives in src/index.css as "R G B" channel strings (e.g.
// `--accent: 42 120 214;`), not hex — this is what lets a utility like
// `border-accent/40` actually apply 40% opacity. Tailwind can't add an alpha
// channel to a flat hex/var() string; it needs `rgb(var(--x) / <alpha>)`. Using
// a plain `"var(--x)"` string here (the earlier version of this file) made any
// `/NN` opacity modifier on a custom color silently resolve to an invalid CSS
// value — see docs/mistakes-log.md.
function withOpacity(variable) {
  return ({ opacityValue }) =>
    opacityValue !== undefined ? `rgb(var(${variable}) / ${opacityValue})` : `rgb(var(${variable}))`;
}

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        page: withOpacity("--page"),
        surface: withOpacity("--surface"),
        "surface-raised": withOpacity("--surface-raised"),
        ink: {
          primary: withOpacity("--ink-primary"),
          secondary: withOpacity("--ink-secondary"),
          muted: withOpacity("--ink-muted"),
        },
        border: "var(--border)", // already a complete rgba(...) — never used with an opacity modifier
        gridline: withOpacity("--gridline"),
        axis: withOpacity("--axis"),
        accent: {
          DEFAULT: withOpacity("--accent"),
          strong: withOpacity("--accent-strong"),
          wash: withOpacity("--accent-wash"),
        },
        good: { DEFAULT: withOpacity("--good"), wash: withOpacity("--good-wash") },
        warning: { DEFAULT: withOpacity("--warning"), wash: withOpacity("--warning-wash") },
        critical: { DEFAULT: withOpacity("--critical"), wash: withOpacity("--critical-wash") },
        // Back-compat aliases used by a couple of older components
        genuine: withOpacity("--good"),
        suspicious: withOpacity("--warning"),
        manipulated: withOpacity("--critical"),
      },
      boxShadow: {
        card: "0 1px 2px rgba(11,11,11,0.04), 0 1px 1px rgba(11,11,11,0.03)",
      },
    },
  },
  plugins: [],
};
