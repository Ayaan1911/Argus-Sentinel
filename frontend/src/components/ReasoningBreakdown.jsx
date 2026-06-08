import React from 'react';

export default function ReasoningBreakdown({ breakdown }) {
  if (!breakdown || breakdown.length === 0) return null;

  const total = breakdown.reduce((acc, step) => acc + step.modifier, 0);

  return (
    <div className="bg-card border border-bordercolor rounded-lg overflow-hidden">
      <div className="bg-surface px-4 py-3 border-b border-bordercolor">
        <h3 className="text-sm font-semibold text-textpri">Why this risk score?</h3>
      </div>
      <div className="p-4 space-y-3">
        {breakdown.map((step, idx) => {
          const mod = step.modifier;
          const isPos = mod > 0;
          return (
            <div key={idx} className="flex gap-4 items-start text-sm pb-3 border-b border-bordercolor last:border-0 last:pb-0">
              <div className={`w-16 shrink-0 font-mono font-bold ${isPos ? 'text-danger' : mod < 0 ? 'text-success' : 'text-textmut'}`}>
                {mod > 0 ? '+' : ''}{mod.toFixed(1)}
              </div>
              <div>
                <div className="font-semibold text-textpri mb-1">{step.label}</div>
                <div className="text-textmut">{step.reason}</div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="bg-surface/50 px-4 py-3 border-t border-bordercolor flex gap-4 text-sm font-bold">
        <div className="w-16 shrink-0 font-mono text-textpri">{total > 0 ? '+' : ''}{total.toFixed(1)}</div>
        <div className="text-textpri">Total Modifier</div>
      </div>
    </div>
  );
}
