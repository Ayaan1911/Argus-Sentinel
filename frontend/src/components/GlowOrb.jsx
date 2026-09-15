import React from 'react';

// Shared visual primitive behind two very different uses:
//   - Landing.jsx: large, `chromatic`, slowly drifting — the hero visual.
//   - Dashboard/FindingDetail: small, single-tone, static — a "risk aura"
//     restrained enough not to fight the data around it.
// One component so the layered-gradient technique isn't duplicated, but the
// two call sites never share layout or copy — see notes.md on why the
// landing page and the dashboard stay structurally separate.
//
// `chromatic` uses the real severity spectrum (blue -> cyan -> amber ->
// orange -> red) as the refracted edge, not an arbitrary new palette.
// `severity` (non-chromatic) ties the whole orb to one real severity color,
// so on the dashboard it's signal — critical glows harder than info — not
// decoration.
const SPECTRUM = ['#3b82f6', '#00d4ff', '#eab308', '#f97316', '#ef4444'];

export default function GlowOrb({ size = 400, chromatic = false, severity, animated = false, className = '' }) {
  const color = severity || '#00d4ff';

  return (
    <div
      className={`pointer-events-none select-none ${animated ? 'animate-orb-drift' : ''} ${className}`}
      style={{ width: size, height: size, position: 'relative' }}
      aria-hidden="true"
    >
      {chromatic ? (
        <>
          {SPECTRUM.map((c, i) => {
            const angle = (i / SPECTRUM.length) * 360;
            const offset = size * 0.16;
            return (
              <div
                key={c}
                className="absolute inset-0 rounded-full"
                style={{
                  background: `radial-gradient(circle, ${c}99 0%, ${c}00 65%)`,
                  transform: `rotate(${angle}deg) translateY(-${offset}px)`,
                  mixBlendMode: 'screen',
                  filter: `blur(${size * 0.12}px)`,
                }}
              />
            );
          })}
          <div
            className="absolute inset-0 rounded-full"
            style={{
              background: 'radial-gradient(circle, #ffffffcc 0%, #00d4ff66 30%, transparent 70%)',
              filter: `blur(${size * 0.05}px)`,
            }}
          />
        </>
      ) : (
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: `radial-gradient(circle, ${color}55 0%, ${color}22 45%, transparent 75%)`,
            filter: `blur(${size * 0.18}px)`,
          }}
        />
      )}
    </div>
  );
}
