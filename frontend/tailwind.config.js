/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f4f0e8",
        surface: "#eee9df",
        card: "#fffdf8",
        bordercolor: "#ccc6ba",
        accent: "#a84e30",
        // Severity colors stay consistent across badges and report charts.
        'sev-critical': "#9b302b",
        'sev-high': "#a44e21",
        'sev-medium': "#856116",
        'sev-low': "#295f91",
        'sev-info': "#4f6664",
        // Process status colors are separate from finding severity.
        danger: "#9b302b",
        warning: "#856116",
        success: "#356b41",
        textpri: "#242720",
        textmut: "#626960",
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        serif: ['"Instrument Serif"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
