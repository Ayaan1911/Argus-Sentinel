import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertTriangle, AlertCircle, Info, ArrowRight, ShieldAlert, ShieldCheck, GitCompare, ChevronDown, ChevronUp } from 'lucide-react';
import client from '../api/client';
import SeverityBadge from '../components/SeverityBadge';
import RiskScore from '../components/RiskScore';
import ReasoningBreakdown from '../components/ReasoningBreakdown';
import AudienceSelector from '../components/AudienceSelector';
import ScanComparison from '../components/ScanComparison';

const STAGE_ORDER = ['subfinder', 'httpx', 'nmap', 'nuclei'];
const STAGE_LABELS = { subfinder: 'Subfinder', httpx: 'Httpx', nmap: 'Nmap', nuclei: 'Nuclei' };
const STAGE_TYPE = { subfinder: 'subdomain', httpx: 'technology', nmap: 'port', nuclei: 'vulnerability' };

function StageStatusBar({ stageStatus, findings }) {
  if (!stageStatus || Object.keys(stageStatus).length === 0) return null;
  return (
    <div className="flex flex-wrap gap-3">
      {STAGE_ORDER.filter(stage => stageStatus[stage]).map(stage => {
        const s = stageStatus[stage];
        const count = findings.filter(f => f.type === STAGE_TYPE[stage]).length;
        const isOk = s.status === 'success';
        return (
          <div
            key={stage}
            className={`px-3 py-2 rounded-md border text-xs font-mono flex items-center gap-2
              ${isOk ? 'bg-success/10 border-success/30 text-success' : 'bg-danger/10 border-danger/30 text-danger'}`}
            title={s.detail || ''}
          >
            <span className="font-bold uppercase">{STAGE_LABELS[stage]}</span>
            <span>
              {isOk ? `succeeded, ${count} found` : `${s.status}${s.detail ? ` (${s.detail})` : ''}`}
            </span>
          </div>
        );
      })}
    </div>
  );
}

const TERMINAL_STATUSES = ['completed', 'failed'];

// Backoff schedule: fast while a scan is likely to finish soon, slower the
// longer it runs, so a long scan doesn't keep hammering the status endpoint.
export function nextPollDelay(elapsedMs) {
  if (elapsedMs < 30000) return 3000;   // first 30s: every 3s
  if (elapsedMs < 120000) return 5000;  // 30s-2min: every 5s
  return 10000;                          // 2min+: every 10s
}

export default function ScanDetail() {
  const { scan_id } = useParams();
  const [scanMeta, setScanMeta] = useState(null); // { target, audience } — from the lightweight status poll
  const [summary, setSummary] = useState(null);
  const [findings, setFindings] = useState([]);
  const [status, setStatus] = useState('pending');
  const [stageStatus, setStageStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [selectedFindingId, setSelectedFindingId] = useState(null);
  const [audience, setAudience] = useState('');
  const [rawOpen, setRawOpen] = useState(false);
  const [scanHistory, setScanHistory] = useState([]);
  const [compareOpen, setCompareOpen] = useState(false);

  const fetchFullScanData = async (target, status) => {
    try {
      const sumRes = await client.get(`/findings/scan/${scan_id}/summary`);
      setSummary(sumRes.data);
      const findRes = await client.get(`/findings/scan/${scan_id}`);
      setFindings(findRes.data);
      if (findRes.data.length > 0 && !selectedFindingId) {
        setSelectedFindingId(findRes.data[0].id);
        if (findRes.data[0].audience_guidance) {
          const keys = Object.keys(findRes.data[0].audience_guidance);
          if (keys.length > 0) setAudience(keys[0]);
        }
      }
    } catch (err) {
      console.error("Failed to fetch full scan data", err);
    }

    // Only meaningful for the "compare to previous scan" section, and only
    // for a completed scan (comparing against a failed one isn't useful and
    // the diff endpoint rejects it) — a failure here shouldn't block the
    // rest of the scan detail page.
    if (status === 'completed') {
      try {
        const histRes = await client.get(`/scans/target/${target}/history`);
        setScanHistory(histRes.data);
      } catch (histErr) {
        console.error("Failed to fetch scan history", histErr);
      }
    }
  };

  useEffect(() => {
    let timeoutId = null;
    let cancelled = false;
    const pollStartTime = Date.now();

    const poll = async () => {
      try {
        const statRes = await client.get(`/scans/${scan_id}/status`);
        if (cancelled) return;

        setScanMeta({ target: statRes.data.target, audience: statRes.data.audience });
        setStatus(statRes.data.status);
        setStageStatus(statRes.data.stage_status || {});
        setLoading(false);

        if (TERMINAL_STATUSES.includes(statRes.data.status)) {
          // Comparison only makes sense for a completed scan — pass status
          // explicitly rather than reading the `status` state var, which
          // hasn't necessarily re-rendered with setStatus above yet.
          await fetchFullScanData(statRes.data.target, statRes.data.status); // fetch the full findings payload exactly once
          return; // terminal — stop polling entirely
        }
      } catch (err) {
        console.error("Failed to check status", err);
        if (err.response?.status === 404) {
          setNotFound(true);
          setLoading(false);
          return; // scan doesn't exist — stop polling
        }
        // transient error (network blip, timeout) — keep polling
      }

      if (!cancelled) {
        timeoutId = setTimeout(poll, nextPollDelay(Date.now() - pollStartTime));
      }
    };

    poll();

    return () => {
      cancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scan_id]);

  // Keyboard navigation — must stay here (before any early returns) to satisfy Rules of Hooks
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!findings.length || !selectedFindingId) return;
      const idx = findings.findIndex(f => f.id === selectedFindingId);
      if (e.key === 'ArrowDown' && idx < findings.length - 1) {
        e.preventDefault();
        setSelectedFindingId(findings[idx + 1].id);
      } else if (e.key === 'ArrowUp' && idx > 0) {
        e.preventDefault();
        setSelectedFindingId(findings[idx - 1].id);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [findings, selectedFindingId]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6 animate-pulse">
        <div className="flex items-center gap-4 border-b border-bordercolor pb-4">
          <div className="w-8 h-8 bg-surface rounded"></div>
          <div className="space-y-2">
            <div className="h-7 w-64 bg-surface rounded"></div>
            <div className="h-4 w-32 bg-surface/70 rounded"></div>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          {[...Array(5)].map((_, i) => <div key={i} className="h-20 bg-surface rounded-lg"></div>)}
        </div>
        <div className="h-2 w-full bg-surface rounded-full"></div>
        <div className="flex gap-6">
          <div className="w-1/3 flex flex-col gap-2">
            {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-surface rounded-lg"></div>)}
          </div>
          <div className="w-2/3 h-96 bg-surface rounded-lg"></div>
        </div>
      </div>
    );
  }
  if (notFound || !scanMeta) return <div className="text-danger">Scan not found</div>;

  const isRunning = status === 'pending' || status === 'running';

  const selectedFinding = findings.find(f => f.id === selectedFindingId);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center gap-4 border-b border-bordercolor pb-4">
        <Link to="/" className="p-2 hover:bg-card rounded-md text-textmut hover:text-textpri transition-colors">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-textpri font-mono">{scanMeta.target}</h2>
            <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold uppercase border
              ${isRunning ? 'bg-warning/20 text-warning border-warning/30 animate-pulse' : ''}
              ${status === 'failed' ? 'bg-danger/20 text-danger border-danger/30' : ''}
              ${status === 'completed' ? 'bg-success/20 text-success border-success/30' : ''}
            `}>
              {status}
            </span>
          </div>
          <p className="text-sm text-textmut mt-1">Audience profile: <span className="text-textpri capitalize">{(scanMeta.audience || '').replace('_', ' ')}</span></p>
        </div>
      </div>

      <StageStatusBar stageStatus={stageStatus} findings={findings} />

      {status === 'completed' && scanHistory.filter(h => h.id !== scan_id).length > 0 && (
        <div className="bg-card border border-bordercolor rounded-lg">
          <button
            onClick={() => setCompareOpen(o => !o)}
            className="w-full flex items-center justify-between px-4 py-3 text-left"
          >
            <span className="flex items-center gap-2 font-semibold text-textpri text-sm">
              <GitCompare size={16} className="text-accent" /> Compare to previous scan
            </span>
            {compareOpen ? <ChevronUp size={16} className="text-textmut" /> : <ChevronDown size={16} className="text-textmut" />}
          </button>
          {compareOpen && (
            <div className="px-4 pb-4 border-t border-bordercolor pt-4">
              <ScanComparison scanId={scan_id} history={scanHistory} />
            </div>
          )}
        </div>
      )}

      {/* Combined risk / severity stats only exist once the scan is terminal
          and the full findings payload has been fetched — see fetchFullScanData. */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="col-span-2 bg-card border border-bordercolor rounded-lg p-4">
            <div className="text-textmut text-xs uppercase font-bold tracking-wider mb-1">Combined Risk</div>
            <div className="text-xl font-bold flex items-center gap-2">
              <SeverityBadge severity={summary.combined_risk_level} />
            </div>
          </div>
          <div className="bg-card/60 backdrop-blur-md border border-sev-critical/30 rounded-lg p-4">
            <div className="text-sev-critical text-xs uppercase font-bold tracking-wider mb-1">Critical</div>
            <div className="text-2xl font-bold font-mono text-textpri">{summary.by_severity.critical}</div>
          </div>
          <div className="bg-card/60 backdrop-blur-md border border-sev-high/30 rounded-lg p-4">
            <div className="text-sev-high text-xs uppercase font-bold tracking-wider mb-1">High</div>
            <div className="text-2xl font-bold font-mono text-textpri">{summary.by_severity.high}</div>
          </div>
          <div className="bg-card/60 backdrop-blur-md border border-sev-medium/30 rounded-lg p-4">
            <div className="text-sev-medium text-xs uppercase font-bold tracking-wider mb-1">Medium</div>
            <div className="text-2xl font-bold font-mono text-textpri">{summary.by_severity.medium}</div>
          </div>
          <div className="bg-card/60 backdrop-blur-md border border-sev-low/30 rounded-lg p-4">
            <div className="text-sev-low text-xs uppercase font-bold tracking-wider mb-1">Low</div>
            <div className="text-2xl font-bold font-mono text-textpri">{summary.by_severity.low}</div>
          </div>
        </div>
      )}

      {/* Severity Distribution Bar */}
      {summary && findings.length > 0 && (
        <div className="h-2 w-full flex rounded-full overflow-hidden bg-surface">
          <div style={{ width: `${(summary.by_severity.critical / findings.length) * 100}%` }} className="bg-sev-critical"></div>
          <div style={{ width: `${(summary.by_severity.high / findings.length) * 100}%` }} className="bg-sev-high"></div>
          <div style={{ width: `${(summary.by_severity.medium / findings.length) * 100}%` }} className="bg-sev-medium"></div>
          <div style={{ width: `${(summary.by_severity.low / findings.length) * 100}%` }} className="bg-sev-low"></div>
          <div style={{ width: `${(summary.by_severity.info / findings.length) * 100}%` }} className="bg-sev-info"></div>
        </div>
      )}

      <div>
        <h3 className="text-xl font-bold text-textpri mb-4">Findings</h3>
        
        {isRunning && findings.length === 0 ? (
          <div className="bg-card/80 backdrop-blur-md border border-bordercolor rounded-lg p-12 text-center flex flex-col items-center">
            <Loader2 className="animate-spin text-accent mb-6" size={32} />
            <h4 className="text-lg font-medium text-textpri mb-4">Scan in Progress</h4>
            
            <div className="flex items-center justify-center gap-3 text-sm font-mono mt-4">
              <span className="text-accent animate-pulse">Subfinder</span>
              <ArrowRight size={14} className="text-textmut" />
              <span className="text-accent animate-pulse" style={{animationDelay: '0.2s'}}>Httpx</span>
              <ArrowRight size={14} className="text-textmut" />
              <span className="text-accent animate-pulse" style={{animationDelay: '0.4s'}}>Nmap</span>
              <ArrowRight size={14} className="text-textmut" />
              <span className="text-accent animate-pulse" style={{animationDelay: '0.6s'}}>Nuclei</span>
            </div>
            
            <p className="text-textmut mt-6 max-w-md">Argus Sentinel is actively discovering and reasoning over the attack surface. Findings will appear once the scan completes.</p>
          </div>
        ) : findings.length === 0 ? (
          <div className="bg-card/80 backdrop-blur-md border border-bordercolor rounded-lg p-12 text-center">
            {status === 'completed' ? (
              <>
                <div className="text-success mb-4 flex justify-center"><ShieldCheck size={40} /></div>
                <div className="text-lg font-medium text-textpri">Target Appears Secure</div>
                <div className="text-textmut mt-2">No vulnerabilities or exposures were detected on this target.</div>
              </>
            ) : status === 'failed' ? (
              <>
                <div className="text-sev-critical mb-2 flex justify-center"><AlertTriangle size={32} /></div>
                <div className="text-lg font-medium text-textpri">Scan Failed</div>
                <div className="text-textmut">The target may be unreachable or the scanners encountered an error.</div>
              </>
            ) : (
              <div className="text-textmut">No findings discovered.</div>
            )}
          </div>
        ) : (
          <div className="flex flex-col lg:flex-row gap-6">
            {/* LEFT PANE: List */}
            <div className="w-full lg:w-1/3 flex flex-col gap-2 max-h-[800px] overflow-y-auto pr-2">
              {findings.map(f => {
                const isSelected = selectedFindingId === f.id;
                let sevBorder = 'border-l-bordercolor';
                if (f.severity === 'critical') sevBorder = 'border-l-sev-critical shadow-sev-critical/10';
                else if (f.severity === 'high') sevBorder = 'border-l-sev-high shadow-sev-high/10';
                else if (f.severity === 'medium') sevBorder = 'border-l-sev-medium shadow-sev-medium/10';
                else if (f.severity === 'low') sevBorder = 'border-l-sev-low shadow-sev-low/10';

                return (
                  <button 
                    key={f.id}
                    onClick={() => {
                      setSelectedFindingId(f.id);
                      if (f.audience_guidance) {
                        const keys = Object.keys(f.audience_guidance);
                        if (keys.length > 0 && !keys.includes(audience)) setAudience(keys[0]);
                      }
                    }}
                    className={`text-left p-4 rounded-r-lg border-y border-r border-l-4 transition-all hover:-translate-y-0.5 hover:shadow-lg focus:outline-none
                      ${isSelected ? 'bg-surface/80 border-y-bordercolor border-r-bordercolor shadow-md ' + sevBorder : 'bg-card border-bordercolor border-l-transparent hover:bg-surface/50'}
                    `}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <SeverityBadge severity={f.severity} />
                      <span className="text-textmut font-mono text-xs font-bold">{f.final_risk_score.toFixed(1)}</span>
                    </div>
                    <div className="font-semibold text-textpri mb-1 line-clamp-1">{f.title}</div>
                    <div className="text-xs text-textmut uppercase tracking-wider font-bold">{f.type}</div>
                  </button>
                );
              })}
            </div>

            {/* RIGHT PANE: Details */}
            {selectedFinding && (
              <div className="w-full lg:w-2/3 bg-card border border-bordercolor rounded-lg p-6 space-y-6 overflow-y-auto max-h-[800px]">
                <div className="flex flex-col md:flex-row gap-8 items-start border-b border-bordercolor pb-6">
                  <div className="flex-1 space-y-4">
                    <div className="flex items-center gap-3">
                      <SeverityBadge severity={selectedFinding.severity} />
                      <span className="text-textmut uppercase tracking-wider text-xs font-bold border border-bordercolor px-2 py-0.5 rounded bg-surface">{selectedFinding.type}</span>
                    </div>
                    <h2 className="text-2xl font-bold text-textpri">{selectedFinding.title}</h2>
                    <p className="text-textmut text-sm">{selectedFinding.technical_impact}</p>
                  </div>
                  <div className="shrink-0 bg-surface border border-bordercolor rounded-xl p-4 flex flex-col items-center gap-2">
                    <div className="text-xs uppercase font-bold text-textmut tracking-wider">Risk Score</div>
                    <RiskScore score={selectedFinding.final_risk_score} />
                    <div className="text-xs text-textmut mt-1">Conf: {(selectedFinding.confidence * 100).toFixed(0)}%</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-6">
                    <ReasoningBreakdown breakdown={selectedFinding.reasoning_breakdown} />
                    
                    {selectedFinding.business_impact && (
                      <div className="bg-surface border border-bordercolor rounded-lg overflow-hidden">
                        <div className="bg-background/50 px-4 py-3 border-b border-bordercolor font-semibold text-sm flex items-center gap-2">
                          <AlertCircle size={16} className="text-warning" /> Business Impact
                        </div>
                        <div className="p-4 text-textpri text-sm">
                          {selectedFinding.business_impact}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="space-y-6">
                    <div className="bg-surface border border-bordercolor rounded-lg overflow-hidden flex flex-col h-full">
                      <div className="bg-background/50 px-4 py-3 border-b border-bordercolor flex justify-between items-center text-sm">
                        <div className="font-semibold flex items-center gap-2">
                          <Info size={16} className="text-accent" /> Targeted Guidance
                        </div>
                      </div>
                      <div className="p-3 border-b border-bordercolor bg-card">
                        <AudienceSelector selected={audience} onChange={setAudience} />
                      </div>
                      <div className="p-4 text-textpri text-sm leading-relaxed whitespace-pre-wrap flex-1">
                        {selectedFinding.audience_guidance?.[audience] || <span className="text-textmut italic">No guidance available for this persona.</span>}
                      </div>
                    </div>
                  </div>
                </div>

                {(selectedFinding.recommended_actions?.length > 0 || selectedFinding.learning_resources?.length > 0) && (
                  <div className="grid grid-cols-1 gap-6 mt-6">
                    {selectedFinding.recommended_actions?.length > 0 && (
                      <div className="bg-surface border border-bordercolor rounded-lg p-5">
                        <h3 className="font-semibold text-textpri mb-3 text-sm flex items-center gap-2"><ShieldAlert size={16} className="text-success" /> Recommended Actions</h3>
                        <ul className="space-y-2">
                          {selectedFinding.recommended_actions.map((act, i) => (
                            <li key={i} className="text-sm text-textmut flex gap-2"><span className="text-success">▹</span> {act}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {selectedFinding.learning_resources?.length > 0 && (
                      <div className="bg-surface border border-bordercolor rounded-lg p-5">
                        <h3 className="font-semibold text-textpri mb-3 text-sm flex items-center gap-2"><ArrowRight size={16} className="text-accent" /> Learning Resources</h3>
                        <ul className="space-y-2">
                          {selectedFinding.learning_resources.map((res, i) => (
                            <li key={i} className="text-sm text-accent hover:underline flex gap-2"><span className="text-textmut">▹</span> <a href={res} target="_blank" rel="noreferrer">{res}</a></li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
