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
      // Glow utilities layered on top of the severity tokens. Deliberately
      // defined ONLY for critical/high/accent/new-in-diff: the *absence* of a
      // glow on medium/low/info is what makes the glow carry hierarchy, so
      // don't add the missing three "for completeness" — that would flatten
      // the signal back out.
      boxShadow: {
        'glow-critical': '0 0 0 1px rgba(239,68,68,0.30), 0 0 28px -6px rgba(239,68,68,0.60)',
        'glow-high': '0 0 0 1px rgba(249,115,22,0.25), 0 0 24px -8px rgba(249,115,22,0.45)',
        'glow-accent': '0 0 0 1px rgba(0,212,255,0.25), 0 0 24px -8px rgba(0,212,255,0.45)',
        'glow-new': '0 0 0 1px rgba(167,139,250,0.30), 0 0 26px -6px rgba(167,139,250,0.55)',
        'glass': 'inset 0 1px 0 0 rgba(255,255,255,0.05), 0 16px 40px -16px rgba(0,0,0,0.75)',
      },
      // The only decorative-looking animation in the app that is actually
      // load-bearing: it fires on critical severity and on NEW diff findings,
      // i.e. exactly the two things a user must not scroll past. Anything
      // that pulses without that meaning behind it does not get this class.
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 0 1px rgba(239,68,68,0.25), 0 0 18px -8px rgba(239,68,68,0.40)' },
          '50%': { boxShadow: '0 0 0 1px rgba(239,68,68,0.45), 0 0 34px -4px rgba(239,68,68,0.75)' },
        },
        'glow-pulse-new': {
          '0%, 100%': { boxShadow: '0 0 0 1px rgba(167,139,250,0.25), 0 0 18px -8px rgba(167,139,250,0.35)' },
          '50%': { boxShadow: '0 0 0 1px rgba(167,139,250,0.45), 0 0 32px -4px rgba(167,139,250,0.65)' },
        },
        // Landing hero orb only — a slow, barely-perceptible drift, not a
        // spin. "Subtle, not gimmicky" per the brief.
        'orb-drift': {
          '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
          '33%': { transform: 'translate(2%, -3%) scale(1.03)' },
          '66%': { transform: 'translate(-2%, 2%) scale(0.98)' },
        },
      },
      animation: {
        'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
        'glow-pulse-new': 'glow-pulse-new 3s ease-in-out infinite',
        'orb-drift': 'orb-drift 16s ease-in-out infinite',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        // Landing page emphasis words only — see Landing.jsx and the
        // "italic serif for emphasis" rule in ARCHITECTURE notes. Never
        // used for body copy or data.
        serif: ['"Instrument Serif"', 'Georgia', 'serif'],
      },
      // The chromatic ribbon: one gradient, reused as the landing page's
      // pipeline connector and (much thinner, once per page) as a header
      // divider on the dashboard. Stops are literally the severity scale
      // plus the accent — not an arbitrary new palette, per the brief.
      backgroundImage: {
        ribbon: 'linear-gradient(90deg, #3b82f6 0%, #00d4ff 22%, #eab308 50%, #f97316 75%, #ef4444 100%)',
      },
    },
  },
  plugins: [],
}
