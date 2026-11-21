import React from 'react';

export default function RiskScore({ score }) {
  return (
    <div className="editorial-risk-score" aria-label={`Risk score ${Number(score || 0).toFixed(1)} out of 10`}>
      <strong>{Number(score || 0).toFixed(1)}</strong>
      <span>/ 10</span>
    </div>
  );
}
