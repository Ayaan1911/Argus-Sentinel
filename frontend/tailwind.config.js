/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0f1a",
        surface: "#111827",
        card: "#1a2235",
        bordercolor: "#1e2d40",
        accent: "#00d4ff",
        danger: "#ff4444",
        warning: "#ffaa00",
        success: "#00ff88",
        textpri: "#e2e8f0",
        textmut: "#64748b",
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', '"Liberation Mono"', '"Courier New"', 'monospace'],
      }
    },
  },
  plugins: [],
}
