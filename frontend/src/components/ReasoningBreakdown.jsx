import React from 'react';
import { Plus, Minus, Gauge } from 'lucide-react';

export default function ReasoningBreakdown({ breakdown }) {
  if (!breakdown || breakdown.length === 0) return null;

  const total = breakdown.reduce((acc, step) => acc + step.modifier, 0);
  const maxMagnitude = Math.max(1, ...breakdown.map(s => Math.abs(s.modifier)));

  return (
    <div className="bg-card border border-bordercolor rounded-lg overflow-hidden">
      <div className="bg-surface px-4 py-3 border-b border-bordercolor flex items-center gap-2">
        <Gauge size={16} className="text-accent" />
        <h3 className="text-sm font-semibold text-textpri">Why this risk score?</h3>
      </div>
      <div className="p-4 space-y-4">
        {breakdown.map((step, idx) => {
          const mod = step.modifier;
          const isPos = mod > 0;
          const isNeg = mod < 0;
          const barPct = (Math.abs(mod) / maxMagnitude) * 100;
          const barColor = isPos ? 'bg-danger' : isNeg ? 'bg-success' : 'bg-bordercolor';
          const textColor = isPos ? 'text-danger' : isNeg ? 'text-success' : 'text-textmut';

          return (
            <div key={idx} className="flex gap-4 items-center text-sm">
              <div className={`w-16 shrink-0 font-mono font-bold flex items-center gap-1 ${textColor}`}>
                {isPos && <Plus size={12} />}
                {isNeg && <Minus size={12} />}
                {Math.abs(mod).toFixed(1)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-textpri truncate">{step.label}</span>
                </div>
                <div className="h-1.5 w-full bg-background rounded-full overflow-hidden mb-1.5">
                  <div className={`h-full rounded-full ${barColor}`} style={{ width: `${barPct}%` }} />
                </div>
                <div className="text-textmut text-xs">{step.reason}</div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="bg-surface/50 px-4 py-3 border-t border-bordercolor flex items-center gap-4 text-sm font-bold">
        <div className="w-16 shrink-0 font-mono text-textpri">{total > 0 ? '+' : ''}{total.toFixed(1)}</div>
        <div className="text-textpri">Total Modifier</div>
      </div>
    </div>
  );
}
