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
        // Severity scale — the ONLY place saturated color should be used to
        // encode meaning. Keep every finding/vuln severity indicator on
        // these five tokens (see SeverityBadge/theme.js) so a scan-detail
        // badge, a dashboard chart slice, and the risk gauge always agree.
        'sev-critical': "#ef4444",
        'sev-high': "#f97316",
        'sev-medium': "#eab308",
        'sev-low': "#3b82f6",
        'sev-info': "#64748b",
        // Generic UI state colors — process/outcome states (scan
        // running/failed/completed, form errors), never a finding severity.
        // danger intentionally matches sev-critical: one red for "bad", not two.
        danger: "#ef4444",
        warning: "#f59e0b",
        success: "#22c55e",
        textpri: "#f1f5f9",
        textmut: "#94a3b8",
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
    },
  },
  plugins: [],
}
