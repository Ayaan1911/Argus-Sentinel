/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'argus-bg': '#0a0f1a',
        'argus-surface': '#111827',
        'argus-card': '#1a2235',
        'argus-border': '#1e2d40',
        'argus-accent': '#00d4ff',
        'argus-danger': '#ff4444',
        'argus-warning': '#ffaa00',
        'argus-success': '#00ff88',
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
      }
    },
  },
  plugins: [],
}
