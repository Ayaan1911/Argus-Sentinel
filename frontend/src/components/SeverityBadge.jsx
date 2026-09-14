import React from 'react';

// The five severity tokens (sev-critical/high/medium/low/info) are the one
// place saturated color carries meaning in this app — every severity
// indicator anywhere (badges, gauges, charts, list borders) must resolve to
// exactly these five, never a one-off hex, so a "critical" reads the same
// color everywhere a user sees it.
const STYLES = {
  critical: 'bg-sev-critical/15 text-sev-critical border-sev-critical/40',
  high: 'bg-sev-high/15 text-sev-high border-sev-high/40',
  medium: 'bg-sev-medium/15 text-sev-medium border-sev-medium/40',
  low: 'bg-sev-low/15 text-sev-low border-sev-low/40',
  informational: 'bg-sev-info/15 text-sev-info border-sev-info/40',
};

const DOT = {
  critical: 'bg-sev-critical',
  high: 'bg-sev-high',
  medium: 'bg-sev-medium',
  low: 'bg-sev-low',
  informational: 'bg-sev-info',
};

export default function SeverityBadge({ severity }) {
  const s = (severity || 'informational').toLowerCase() === 'info' ? 'informational' : (severity || 'informational').toLowerCase();
  const style = STYLES[s] || STYLES.informational;
  const dot = DOT[s] || DOT.informational;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase border ${style}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      {s === 'informational' ? 'INFO' : s}
    </span>
  );
}
