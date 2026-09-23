import React from 'react';

// Exported so the landing page can list the same 5 real personas without
// re-typing them — one source of truth for what Argus actually supports.
export const AUDIENCES = [
  { id: 'student', label: 'Student' },
  { id: 'developer', label: 'Developer' },
  { id: 'bug_bounty_hunter', label: 'Bug Bounty Hunter' },
  { id: 'pentester', label: 'Pentester' },
  { id: 'security_team', label: 'Security Professional' },
];

export default function AudienceSelector({ selected, onChange }) {
  return (
    <div role="tablist" aria-label="Audience persona" className="inline-flex flex-wrap gap-1 bg-background border border-bordercolor rounded-lg p-1">
      {AUDIENCES.map((aud) => (
        <button
          key={aud.id}
          type="button"
          role="tab"
          aria-selected={selected === aud.id}
          onClick={() => onChange(aud.id)}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            selected === aud.id
              ? 'bg-accent text-background font-bold shadow-glow-accent'
              : 'text-textmut hover:text-textpri hover:bg-card'
          }`}
        >
          {aud.label}
        </button>
      ))}
    </div>
  );
}
