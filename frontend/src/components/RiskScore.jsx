import React, { useState, useEffect } from 'react';
import { severityColor } from '../theme';

function scoreToSeverityLabel(score) {
  if (score >= 8.0) return 'critical';
  if (score >= 6.0) return 'high';
  if (score >= 4.0) return 'medium';
  if (score > 2.0) return 'low';
  return 'informational';
}

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

  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (displayScore / 10) * circumference;
  const box = 100;

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <div
        className="absolute inset-3 rounded-full blur-md opacity-25"
        style={{ backgroundColor: color }}
        aria-hidden="true"
      />
      <svg viewBox={`0 0 ${box} ${box}`} className="relative -rotate-90 w-full h-full">
        <circle cx={box / 2} cy={box / 2} r={radius} stroke="currentColor" strokeWidth="8" fill="transparent" className="text-bordercolor" />
        <circle
          cx={box / 2}
          cy={box / 2}
          r={radius}
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: 'stroke-dashoffset 16ms linear' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-2xl font-bold font-mono leading-none" style={{ color }}>{displayScore.toFixed(1)}</span>
        <span className="text-[10px] text-textmut font-mono mt-1">/ 10</span>
        <span className="text-[9px] font-bold uppercase tracking-wider mt-1" style={{ color }}>
          {label === 'informational' ? 'info' : label}
        </span>
      </div>
    </div>
  );
}
