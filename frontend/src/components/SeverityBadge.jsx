import React from 'react';

export default function SeverityBadge({ severity }) {
  const s = (severity || 'informational').toLowerCase();
  let colorClass = 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  
  if (s === 'critical') colorClass = 'bg-danger/20 text-danger border-danger/30';
  else if (s === 'high') colorClass = 'bg-[#ff6b00]/20 text-[#ff6b00] border-[#ff6b00]/30';
  else if (s === 'medium') colorClass = 'bg-warning/20 text-warning border-warning/30';
  else if (s === 'low') colorClass = 'bg-blue-500/20 text-blue-400 border-blue-500/30';

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase border ${colorClass}`}>
      {s === 'informational' ? 'INFO' : s}
    </span>
  );
}
