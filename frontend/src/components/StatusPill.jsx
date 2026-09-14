import React from 'react';
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';

// Generic process/outcome state pill — scan status, per-tool stage status.
// Deliberately separate from SeverityBadge: these colors mean "did the
// pipeline succeed", never "how bad is this finding", so they must never
// borrow the sev-* palette (that would make a "running" scan look like a
// medium-severity finding at a glance).
const CONFIG = {
  pending: { label: 'pending', className: 'bg-surface text-textmut border-bordercolor', Icon: Clock },
  running: { label: 'running', className: 'bg-warning/15 text-warning border-warning/40 animate-pulse', Icon: Loader2, spin: true },
  completed: { label: 'completed', className: 'bg-success/15 text-success border-success/40', Icon: CheckCircle2 },
  success: { label: 'success', className: 'bg-success/15 text-success border-success/40', Icon: CheckCircle2 },
  failed: { label: 'failed', className: 'bg-danger/15 text-danger border-danger/40', Icon: XCircle },
};

export default function StatusPill({ status, children, size = 'sm' }) {
  const cfg = CONFIG[status] || CONFIG.pending;
  const { Icon } = cfg;
  const sizeClass = size === 'sm' ? 'px-2.5 py-1 text-xs gap-1.5' : 'px-3 py-1.5 text-sm gap-2';

  return (
    <span className={`inline-flex items-center rounded-full font-mono font-bold uppercase border ${sizeClass} ${cfg.className}`}>
      <Icon size={size === 'sm' ? 12 : 14} className={cfg.spin ? 'animate-spin' : ''} />
      {children || cfg.label}
    </span>
  );
}
