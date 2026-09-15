import React, { useState, useEffect } from 'react';
import { severityColor } from '../theme';

function scoreToSeverityLabel(score) {
  if (score >= 8.0) return 'critical';
  if (score >= 6.0) return 'high';
  if (score >= 4.0) return 'medium';
  if (score > 2.0) return 'low';
  return 'informational';
}

// 270° instrument sweep (gap at the bottom) rather than a closed ring: an
// open arc has an unambiguous "empty" end, so a 3.1 and a 9.4 are
// distinguishable by shape alone at thumbnail size, before the number is
// legible at all.
const SWEEP = 0.75;
const RADIUS = 40;
const BOX = 100;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const ARC = CIRCUMFERENCE * SWEEP;
const TICKS = 10;

export default function RiskScore({ score, size = 96 }) {
  const targetScore = parseFloat(score || 0);
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    let start = 0;
    const duration = 500; // ms
    const increment = targetScore / (duration / 16); // ~60fps

    if (targetScore === 0) {
      setDisplayScore(0);
      return;
    }

    const timer = setInterval(() => {
      start += increment;
      if (start >= targetScore) {
        setDisplayScore(targetScore);
        clearInterval(timer);
      } else {
        setDisplayScore(start);
      }
    }, 16);

    return () => clearInterval(timer);
  }, [targetScore]);

  const label = scoreToSeverityLabel(targetScore);
  const color = severityColor(label);
  const filled = Math.min(1, Math.max(0, displayScore / 10));
  const strokeDashoffset = ARC * (1 - filled);

  // Glow intensity is itself a severity channel: critical pulses, high sits
  // at a steady strong glow, medium is faint, low/info don't glow at all.
  // Read the ramp top-to-bottom — the drop-off is the hierarchy.
  const glow =
    label === 'critical' ? 0.85 :
    label === 'high' ? 0.6 :
    label === 'medium' ? 0.35 : 0;

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      {glow > 0 && (
        <div
          className={`absolute inset-[18%] rounded-full blur-xl ${label === 'critical' ? 'animate-pulse' : ''}`}
          style={{ backgroundColor: color, opacity: glow * 0.45 }}
          aria-hidden="true"
        />
      )}
      <svg
        viewBox={`0 0 ${BOX} ${BOX}`}
        className="relative w-full h-full"
        style={{ transform: 'rotate(135deg)' }}
        aria-hidden="true"
      >
        {/* Tick ring — reads as a calibrated instrument rather than a
            generic progress donut. Ticks past the current value stay dim. */}
        {Array.from({ length: TICKS + 1 }, (_, i) => {
          const angle = (i / TICKS) * SWEEP * 2 * Math.PI;
          const inner = RADIUS + 8;
          const outer = RADIUS + (i % 5 === 0 ? 13 : 11);
          const cx = BOX / 2;
          const passed = i / TICKS <= filled;
          return (
            <line
              key={i}
              x1={cx + inner * Math.cos(angle)}
              y1={cx + inner * Math.sin(angle)}
              x2={cx + outer * Math.cos(angle)}
              y2={cx + outer * Math.sin(angle)}
              stroke={passed ? color : '#242d3a'}
              strokeWidth={i % 5 === 0 ? 2 : 1}
              strokeLinecap="round"
              opacity={passed ? 0.9 : 0.6}
            />
          );
        })}
        <circle
          cx={BOX / 2}
          cy={BOX / 2}
          r={RADIUS}
          stroke="#1a222e"
          strokeWidth="9"
          strokeLinecap="round"
          fill="transparent"
          strokeDasharray={`${ARC} ${CIRCUMFERENCE}`}
        />
        <circle
          cx={BOX / 2}
          cy={BOX / 2}
          r={RADIUS}
          stroke={color}
          strokeWidth="9"
          strokeLinecap="round"
          fill="transparent"
          strokeDasharray={`${ARC} ${CIRCUMFERENCE}`}
          strokeDashoffset={strokeDashoffset}
          style={{
            transition: 'stroke-dashoffset 16ms linear',
            filter: glow > 0 ? `drop-shadow(0 0 ${6 * glow}px ${color})` : 'none',
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center leading-none">
        <span
          className="font-mono font-extrabold tabular-nums tracking-tighter"
          style={{ color, fontSize: size * 0.34, textShadow: glow > 0 ? `0 0 ${18 * glow}px ${color}66` : 'none' }}
        >
          {displayScore.toFixed(1)}
        </span>
        <span className="text-textmut font-mono mt-1" style={{ fontSize: Math.max(9, size * 0.085) }}>/ 10</span>
        <span
          className="font-bold uppercase tracking-[0.15em] mt-1.5"
          style={{ color, fontSize: Math.max(8, size * 0.075) }}
        >
          {label === 'informational' ? 'info' : label}
        </span>
      </div>
    </div>
  );
}
