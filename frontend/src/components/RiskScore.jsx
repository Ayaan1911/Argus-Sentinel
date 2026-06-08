import React from 'react';

export default function RiskScore({ score }) {
  const s = parseFloat(score || 0);
  let color = '#00ff88'; // green
  if (s >= 8.0) color = '#ff4444'; // red
  else if (s >= 6.0) color = '#ff6b00'; // orange
  else if (s >= 4.0) color = '#ffaa00'; // yellow

  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (s / 10) * circumference;

  return (
    <div className="relative flex items-center justify-center w-24 h-24">
      <svg className="transform -rotate-90 w-24 h-24">
        <circle
          cx="48"
          cy="48"
          r={radius}
          stroke="currentColor"
          strokeWidth="6"
          fill="transparent"
          className="text-bordercolor"
        />
        <circle
          cx="48"
          cy="48"
          r={radius}
          stroke={color}
          strokeWidth="6"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-2xl font-bold font-mono text-textpri" style={{ color }}>{s.toFixed(1)}</span>
        <span className="text-xs text-textmut font-mono">/10</span>
      </div>
    </div>
  );
}
