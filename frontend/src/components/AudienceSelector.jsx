import React from 'react';

export default function AudienceSelector({ selected, onChange }) {
  const audiences = [
    { id: 'student', label: 'Student' },
    { id: 'developer', label: 'Developer' },
    { id: 'bug_bounty_hunter', label: 'Bug Bounty Hunter' },
    { id: 'pentester', label: 'Pentester' },
    { id: 'security_team', label: 'Security Professional' },
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {audiences.map((aud) => (
        <button
          key={aud.id}
          onClick={() => onChange(aud.id)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors border ${
            selected === aud.id
              ? 'bg-accent/20 border-accent/50 text-accent'
              : 'bg-card border-bordercolor text-textmut hover:bg-surface hover:text-textpri'
          }`}
        >
          {aud.label}
        </button>
      ))}
    </div>
  );
}
