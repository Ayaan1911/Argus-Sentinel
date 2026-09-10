import React, { useEffect, useRef, useState } from 'react';
import { ChevronDown, ChevronUp, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import client from '../api/client';
import SeverityBadge from './SeverityBadge';

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

function FindingRow({ finding, badge, badgeClass, muted }) {
  return (
    <div className={`flex items-center justify-between gap-3 px-3 py-2 rounded-md border border-bordercolor bg-card ${muted ? 'opacity-50' : ''}`}>
      <div className="min-w-0 flex-1">
        <div className={`text-sm font-medium text-textpri truncate ${muted ? 'line-through' : ''}`}>{finding.title}</div>
        <div className="text-xs text-textmut uppercase tracking-wider">{finding.type}</div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {badge && (
          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${badgeClass}`}>
            {badge}
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
            className="bg-surface border border-bordercolor rounded-md px-2 py-1 text-textpri font-mono text-xs"
          >
            {otherScans.map(h => (
              <option key={h.id} value={h.id}>
                {new Date(h.created_at).toLocaleString()} ({h.finding_count} findings)
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="text-sm font-mono text-textpri">
        <span className="text-success font-bold">{summary.new} new</span>
        <span className="text-textmut mx-2">·</span>
        <span className="text-textmut font-bold">{summary.resolved} resolved</span>
        <span className="text-textmut mx-2">·</span>
        <span className="text-warning font-bold">{summary.changed} changed</span>
        <span className="text-textmut mx-2">·</span>
        <span className="text-textmut">{summary.unchanged} unchanged</span>
      </div>

      {new_findings.length > 0 && (
        <div className="space-y-2">
          {new_findings.map(f => (
            <div key={f.id} className="border-l-4 border-l-success rounded-r-md overflow-hidden">
              <FindingRow finding={f} badge="NEW" badgeClass="bg-success/20 text-success border-success/30" />
            </div>
          ))}
        </div>
      )}

      {changed_findings.length > 0 && (
        <div className="space-y-2">
          {changed_findings.map(c => (
            <div key={c.finding.id} className="flex items-center justify-between gap-3 px-3 py-2 rounded-md border border-warning/30 bg-warning/5">
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium text-textpri truncate">{c.finding.title}</div>
                <div className="text-xs text-textmut uppercase tracking-wider">{c.finding.type}</div>
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
          {resolved_findings.map(f => (
            <div key={f.id} className="border-l-4 border-l-bordercolor rounded-r-md overflow-hidden">
              <FindingRow finding={f} badge="RESOLVED" badgeClass="bg-surface text-textmut border-bordercolor" muted />
            </div>
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
