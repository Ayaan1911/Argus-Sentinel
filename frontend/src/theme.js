// Mirrors severity tokens in tailwind.config.js for SVG fills that need hex.

export const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  informational: '#64748b',
  info: '#64748b',
};

export function severityColor(severity) {
  return SEVERITY_COLORS[(severity || 'informational').toLowerCase()] || SEVERITY_COLORS.informational;
}
