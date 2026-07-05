import React, { useState, useEffect } from 'react';

export default function RiskScore({ score }) {
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

  let color = '#3b82f6'; // low (blue)
  if (targetScore >= 8.0) color = '#ef4444'; // critical (red)
  else if (targetScore >= 6.0) color = '#f97316'; // high (orange)
  else if (targetScore >= 4.0) color = '#eab308'; // medium (yellow)

  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  // Animate the circle stroke based on displayScore too!
  const strokeDashoffset = circumference - (displayScore / 10) * circumference;

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
          style={{ transition: 'stroke-dashoffset 16ms linear' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-2xl font-bold font-mono text-textpri" style={{ color }}>{displayScore.toFixed(1)}</span>
        <span className="text-xs text-textmut font-mono">/10</span>
      </div>
    </div>
  );
}
