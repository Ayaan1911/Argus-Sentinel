import React from 'react';
import { Plus, Minus, Gauge } from 'lucide-react';

// `reasoning_breakdown[0]` is always the base score, not a modifier — see
// engines/reasoning.py, which seeds the array with
// {label: "Base Score", modifier: base_score} before appending real
// modifiers. Summing the whole array therefore yields the *final* score, not
// the total modifier. The footer below sums only the rows after the base, so
// the number under the "Total Modifier" label is actually a total modifier.
// Guarded by the label check rather than index alone so a breakdown that
// ever arrives without a base row still renders every row as a modifier.
function splitBreakdown(breakdown) {
  const hasBase = breakdown[0] && breakdown[0].label === 'Base Score';
  return {
    base: hasBase ? breakdown[0] : null,
    modifiers: hasBase ? breakdown.slice(1) : breakdown,
  };
}

export default function ReasoningBreakdown({ breakdown }) {
  if (!breakdown || breakdown.length === 0) return null;

  const { base, modifiers } = splitBreakdown(breakdown);
  const total = modifiers.reduce((acc, step) => acc + step.modifier, 0);
  const maxMagnitude = Math.max(1, ...modifiers.map(s => Math.abs(s.modifier)));
  const totalPos = total > 0;
  const totalNeg = total < 0;

  return (
    <div className="glass rounded-xl overflow-hidden">
      <div className="bg-surface/60 px-4 py-3 border-b border-white/[0.06] flex items-center gap-2">
        <Gauge size={16} className="text-accent" />
        {/* The one header in this component that gets the landing page's
            bold-sans + italic-serif pairing — this panel is the app's actual
            differentiator, so it's the deliberate exception to the
            uppercase-tracking-label style every sibling panel header uses. */}
        <h3 className="text-sm font-bold text-textpri">
          Why this <em className="font-serif italic font-normal text-accent">risk score</em>?
        </h3>
      </div>

      {base && (
        <div className="px-4 py-3 border-b border-white/[0.06] flex gap-4 items-center">
          <div className="w-16 shrink-0 font-mono font-extrabold text-lg tabular-nums text-textpri">
            {base.modifier.toFixed(1)}
          </div>
          <div className="min-w-0">
            <div className="font-semibold text-textpri text-sm">{base.label}</div>
            <div className="text-textmut text-xs mt-0.5">{base.reason}</div>
          </div>
        </div>
      )}

      {modifiers.length > 0 ? (
        <div className="p-4 space-y-4">
          {modifiers.map((step, idx) => {
            const mod = step.modifier;
            const isPos = mod > 0;
            const isNeg = mod < 0;
            const barPct = (Math.abs(mod) / maxMagnitude) * 100;
            // The single largest contributor is the one line of the
            // explanation a user actually needs — give only it the glow, so
            // the eye lands there instead of scanning every row equally.
            const isDominant = Math.abs(mod) === maxMagnitude && mod !== 0;
            const barColor = isPos ? 'bg-danger' : isNeg ? 'bg-success' : 'bg-bordercolor';
            const textColor = isPos ? 'text-danger' : isNeg ? 'text-success' : 'text-textmut';

            return (
              <div key={idx} className="flex gap-4 items-center text-sm">
                <div className={`w-16 shrink-0 font-mono font-extrabold text-lg tabular-nums flex items-center gap-0.5 ${textColor}`}>
                  {isPos && <Plus size={14} strokeWidth={3} />}
                  {isNeg && <Minus size={14} strokeWidth={3} />}
                  {Math.abs(mod).toFixed(1)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-semibold text-textpri truncate">{step.label}</span>
                  </div>
                  <div className="h-2 w-full bg-background/80 rounded-full overflow-hidden mb-1.5 ring-1 ring-inset ring-white/[0.04]">
                    <div
                      className={`h-full rounded-full ${barColor} transition-[width] duration-500`}
                      style={{
                        width: `${barPct}%`,
                        boxShadow: isDominant
                          ? `0 0 12px ${isPos ? 'rgba(239,68,68,0.75)' : 'rgba(34,197,94,0.75)'}`
                          : 'none',
                      }}
                    />
                  </div>
                  <div className="text-textmut text-xs">{step.reason}</div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="px-4 py-3 text-xs text-textmut">
          No correlation modifiers applied — this finding scored on its base alone.
        </div>
      )}

      {/* The payoff line. Everything above is the argument; this is the
          verdict, so it gets the only heavyweight type and glow in the panel.
          It glows only when context actually moved the score — a net-zero
          modifier stays deliberately flat. */}
      <div
        className={`px-4 py-4 border-t flex items-center gap-4 ${
          totalPos ? 'border-danger/30 bg-danger/[0.07]'
            : totalNeg ? 'border-success/30 bg-success/[0.07]'
            : 'border-white/[0.06] bg-surface/40'
        }`}
      >
        <div
          className={`w-16 shrink-0 font-mono font-black text-3xl tabular-nums tracking-tighter ${
            totalPos ? 'text-danger' : totalNeg ? 'text-success' : 'text-textmut'
          }`}
          style={{
            textShadow: totalPos ? '0 0 22px rgba(239,68,68,0.55)'
              : totalNeg ? '0 0 22px rgba(34,197,94,0.45)'
              : 'none',
          }}
        >
          {totalPos ? '+' : totalNeg ? '−' : ''}{Math.abs(total).toFixed(1)}
        </div>
        <div>
          <div className="text-textpri font-bold uppercase tracking-[0.12em] text-xs">Total Modifier</div>
          <div className="text-textmut text-xs mt-0.5">
            {totalPos ? 'Context raised this score above its base'
              : totalNeg ? 'Context lowered this score below its base'
              : 'Context left the base score unchanged'}
          </div>
        </div>
      </div>
    </div>
  );
}
