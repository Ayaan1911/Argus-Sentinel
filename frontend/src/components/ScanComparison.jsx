import React, { useEffect, useRef, useState } from 'react';
import { ChevronDown, ChevronUp, ArrowUpRight, ArrowDownRight, Minus, Plus, CheckCheck, RefreshCw } from 'lucide-react';
import client from '../api/client';
import SeverityBadge from './SeverityBadge';

// Diff states are a different axis of meaning than finding severity, so they
// deliberately borrow neither the sev-* palette nor pure success/danger:
// violet = "new" (attention, not itself a verdict), accent = "changed"
// (something to look at), muted gray = "resolved" (done, fading out).
// "This scan caught something new" is the one frame that sells the diffing
// feature with no surrounding context, so NEW is the only state that gets the
// full glass + glow + pulse treatment. CHANGED is a steady accent glow and
// RESOLVED is deliberately the dimmest thing on the page — the contrast
// between the three is what makes the state readable in a screenshot.
const DIFF_STYLE = {
  new: {
    border: 'border-l-violet-400',
    row: 'glass shadow-glow-new animate-glow-pulse-new',
    badge: 'bg-violet-400/20 text-violet-200 border-violet-400/60 shadow-glow-new',
    icon: Plus,
  },
  changed: {
    border: 'border-l-accent',
    row: 'bg-accent/[0.06] border-bordercolor',
    badge: 'bg-accent/20 text-accent border-accent/50',
    icon: RefreshCw,
  },
  resolved: {
    border: 'border-l-bordercolor',
    row: 'bg-card/40 border-bordercolor',
    badge: 'bg-surface text-textmut border-bordercolor',
    icon: CheckCheck,
  },
};

function GroupHeading({ children, count, tone }) {
  return (
    <div className="flex items-center gap-3 pt-2">
      <span className={`text-[11px] font-bold uppercase tracking-[0.22em] ${tone}`}>{children}</span>
      <span className="font-mono text-xs text-textmut tabular-nums">{count}</span>
      <span className="h-px flex-1 bg-gradient-to-r from-bordercolor to-transparent" />
    </div>
  );
}

function ScoreDelta({ previous, next }) {
  const delta = next - previous;
  if (delta === 0) {
    return (
      <span className="inline-flex items-center gap-1 font-mono text-xs text-textmut">
        <Minus size={12} /> {previous.toFixed(1)} → {next.toFixed(1)}
      </span>
    );
  }
  const worse = delta > 0;
  return (
    <span className={`inline-flex items-center gap-1 font-mono text-xs font-bold ${worse ? 'text-sev-critical' : 'text-success'}`}>
      {worse ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
      {previous.toFixed(1)} → {next.toFixed(1)}
    </span>
  );
}

function FindingRow({ finding, state, muted }) {
  const style = state ? DIFF_STYLE[state] : null;
  const Icon = style?.icon;
  return (
    <div className={`flex items-center justify-between gap-3 px-4 py-3 rounded-lg border ${style ? `border-l-4 ${style.border} ${style.row}` : 'border-bordercolor bg-card'} ${muted ? 'opacity-60' : ''}`}>
      <div className="min-w-0 flex-1">
        <div className={`text-sm font-semibold text-textpri truncate ${muted ? 'line-through decoration-textmut' : ''}`}>{finding.title}</div>
        <div className="text-[10px] text-textmut uppercase tracking-[0.18em] font-bold mt-0.5">{finding.type}</div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {style && (
          // NOTE: the badge's text content must stay exactly the uppercased
          // state ("NEW"/"RESOLVED") — ScanComparison.test.jsx matches it with
          // getByText on exact text, so a CSS-only uppercase or extra text
          // node in here would break those assertions silently.
          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-mono font-black tracking-[0.1em] border ${style.badge}`}>
            {Icon && <Icon size={11} strokeWidth={3} />}
            {state.toUpperCase()}
          </span>
        )}
        <SeverityBadge severity={finding.severity} />
      </div>
    </div>
  );
}

export default function ScanComparison({ scanId, history }) {
  const [compareToId, setCompareToId] = useState(null);
  const [diff, setDiff] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [unchangedOpen, setUnchangedOpen] = useState(false);
  const requestIdRef = useRef(0);

  const fetchDiff = (compareTo) => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);

    const url = `/scans/${scanId}/diff` + (compareTo ? `?compare_to=${compareTo}` : '');
    client.get(url)
      .then(res => {
        if (requestIdRef.current !== requestId) return; // a newer request has since superseded this one
        setDiff(res.data);
        // Sync the picker to whichever scan the backend actually compared
        // against, including its own default choice on first load.
        setCompareToId(res.data.compared_to_scan_id);
      })
      .catch(err => {
        if (requestIdRef.current !== requestId) return;
        setError(err.response?.data?.detail || 'Failed to load comparison');
      })
      .finally(() => {
        if (requestIdRef.current === requestId) setLoading(false);
      });
  };

  useEffect(() => {
    fetchDiff(null); // initial load — let the backend pick the default comparison
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanId]);

  if (loading && !diff) {
    return <div className="text-textmut text-sm py-4">Loading comparison…</div>;
  }
  if (error) {
    return <div className="text-danger text-sm py-4">{error}</div>;
  }
  if (!diff) return null;

  const { summary, new_findings, resolved_findings, changed_findings, unchanged_findings } = diff;
  const otherScans = history.filter(h => h.id !== scanId);

  return (
    <div className="space-y-4">
      {otherScans.length >= 2 && (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-textmut">Compare against:</span>
          <select
            value={compareToId || ''}
            onChange={e => { setCompareToId(e.target.value); fetchDiff(e.target.value); }}
            className="glass-solid rounded-md px-2 py-1.5 text-textpri font-mono text-xs"
          >
            {otherScans.map(h => (
              <option key={h.id} value={h.id}>
                {new Date(h.created_at).toLocaleString()} ({h.finding_count} findings)
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3 text-base font-mono">
        <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl border font-black tracking-tight ${
          summary.new > 0
            ? 'bg-violet-400/15 border-violet-400/50 text-violet-200 shadow-glow-new animate-glow-pulse-new'
            : 'bg-surface border-bordercolor text-textmut'
        }`}><Plus size={16} strokeWidth={3} /> {summary.new} new</span>
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface border border-bordercolor text-textmut font-bold"><CheckCheck size={16} /> {summary.resolved} resolved</span>
        <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl border font-bold ${
          summary.changed > 0 ? 'bg-accent/15 border-accent/50 text-accent shadow-glow-accent' : 'bg-surface border-bordercolor text-textmut'
        }`}><RefreshCw size={16} /> {summary.changed} changed</span>
        <span className="text-textmut text-sm">{summary.unchanged} unchanged</span>
      </div>

      {new_findings.length > 0 && (
        <div className="space-y-2">
          <GroupHeading count={new_findings.length} tone="text-violet-300">New findings</GroupHeading>
          {new_findings.map(f => (
            <FindingRow key={f.id} finding={f} state="new" />
          ))}
        </div>
      )}

      {changed_findings.length > 0 && (
        <div className="space-y-2">
          <GroupHeading count={changed_findings.length} tone="text-accent">Changed findings</GroupHeading>
          {changed_findings.map(c => (
            <div key={c.finding.id} className="flex items-center justify-between gap-3 px-4 py-3 rounded-lg border border-bordercolor border-l-4 border-l-accent bg-accent/[0.06]">
              <div className="min-w-0 flex-1">
                <div className="text-sm font-semibold text-textpri truncate">{c.finding.title}</div>
                <div className="text-[10px] text-textmut uppercase tracking-[0.18em] font-bold mt-0.5">{c.finding.type}</div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <ScoreDelta previous={c.previous_risk_score} next={c.finding.final_risk_score} />
                <SeverityBadge severity={c.finding.severity} />
              </div>
            </div>
          ))}
        </div>
      )}

      {resolved_findings.length > 0 && (
        <div className="space-y-2">
          <GroupHeading count={resolved_findings.length} tone="text-textmut">Resolved findings</GroupHeading>
          {resolved_findings.map(f => (
            <FindingRow key={f.id} finding={f} state="resolved" muted />
          ))}
        </div>
      )}

      {unchanged_findings.length > 0 && (
        <div>
          <button
            onClick={() => setUnchangedOpen(o => !o)}
            className="flex items-center gap-2 text-sm text-textmut hover:text-textpri transition-colors"
          >
            {unchangedOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            {unchanged_findings.length} unchanged finding{unchanged_findings.length === 1 ? '' : 's'}
          </button>
          {unchangedOpen && (
            <div className="space-y-2 mt-2">
              {unchanged_findings.map(f => (
                <FindingRow key={f.id} finding={f} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
