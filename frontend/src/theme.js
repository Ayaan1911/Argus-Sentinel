// Mirrors the color tokens in tailwind.config.js, for the few contexts that
// can't consume a Tailwind class (recharts props, raw SVG stroke/fill) and
// need a real hex string instead. Keep values in sync with tailwind.config.js
// by hand — there's no build step that shares them automatically.

export const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  informational: '#64748b',
  info: '#64748b',
};

export const STATE_COLORS = {
  accent: '#00d4ff',
  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444',
};

// Chart neutrals — grid lines, axis text, tooltip chrome. Kept in the same
// restrained near-monochrome range as the rest of the UI so severity/series
// colors are what actually stands out.
export const CHART_NEUTRAL = {
  grid: '#242d3a',
  axisText: '#64748b',
  tooltipBg: '#171d27',
  tooltipBorder: '#242d3a',
};

// Distinct from the severity scale on purpose — finding *type* is a
// different axis of meaning than finding *severity*, so it gets its own
// palette rather than borrowing red/orange/yellow.
export const TYPE_COLORS = {
  vulnerability: '#00d4ff',
  port: '#3b82f6',
  subdomain: '#a78bfa',
  technology: '#f472b6',
};

export function severityColor(severity) {
  return SEVERITY_COLORS[(severity || 'informational').toLowerCase()] || SEVERITY_COLORS.informational;
}
