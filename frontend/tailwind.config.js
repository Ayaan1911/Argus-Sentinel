/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0e14",
        surface: "#11151c",
        card: "#171d27",
        bordercolor: "#242d3a",
        accent: "#00d4ff",
        'sev-critical': "#ef4444",
        'sev-high': "#f97316",
        'sev-medium': "#eab308",
        'sev-low': "#3b82f6",
        'sev-info': "#64748b",
        textpri: "#f1f5f9",
        textmut: "#94a3b8",
      }
    },
  },
  plugins: [],
}
