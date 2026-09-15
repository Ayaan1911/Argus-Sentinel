import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Server, Activity, ShieldAlert, GraduationCap, ChevronDown, ChevronUp } from 'lucide-react';
import client from '../api/client';
import SeverityBadge from '../components/SeverityBadge';
import RiskScore from '../components/RiskScore';
import ReasoningBreakdown from '../components/ReasoningBreakdown';
import AudienceSelector from '../components/AudienceSelector';

// The gauge panel is the single most visually weighted element in the app —
// the explained risk score is the product's actual differentiator. Its glow
// is keyed to the finding's own severity, and only critical pulses, so the
// treatment itself communicates "drop what you're doing" vs "read later".
const PANEL_GLOW = {
  critical: 'shadow-glow-critical animate-glow-pulse',
  high: 'shadow-glow-high',
  medium: '',
  low: '',
  informational: '',
  info: '',
};

function FindingDetailSkeleton() {
  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12 animate-pulse">
      <div className="flex items-center gap-4 pb-2 border-b border-bordercolor">
        <div className="w-9 h-9 bg-surface rounded-md" />
        <div className="h-4 w-32 bg-surface rounded" />
      </div>
      <div className="flex flex-col md:flex-row gap-8 items-start">
        <div className="flex-1 space-y-4 w-full">
          <div className="h-6 w-40 bg-surface rounded-full" />
          <div className="h-8 w-3/4 bg-surface rounded" />
          <div className="h-4 w-1/2 bg-surface rounded" />
        </div>
        <div className="shrink-0 w-32 h-32 bg-surface rounded-xl" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
        <div className="h-48 bg-surface rounded-lg" />
        <div className="h-48 bg-surface rounded-lg" />
      </div>
    </div>
  );
}

export default function FindingDetail() {
  const { scan_id, finding_id } = useParams();
  const [finding, setFinding] = useState(null);
  const [audience, setAudience] = useState('');
  const [loading, setLoading] = useState(true);
  const [rawOpen, setRawOpen] = useState(false);

  useEffect(() => {
    client.get(`/findings/${finding_id}`)
      .then(res => {
        setFinding(res.data);
        if (res.data.audience_guidance) {
          const keys = Object.keys(res.data.audience_guidance);
          if (keys.length > 0) setAudience(keys[0]);
        }
        setLoading(false);
      })
      .catch(err => setLoading(false));
  }, [finding_id]);

  if (loading) return <FindingDetailSkeleton />;
  if (!finding) return <div className="text-danger">Finding not found</div>;

  const severityGlow = PANEL_GLOW[(finding.severity || 'informational').toLowerCase()] || '';

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      <div className="flex items-center gap-4 pb-2 border-b border-bordercolor">
        <Link to={`/scan/${scan_id}`} className="p-2 hover:bg-card rounded-md text-textmut hover:text-textpri transition-colors">
          <ArrowLeft size={20} />
        </Link>
        <div className="text-textmut font-mono text-sm uppercase tracking-wider font-semibold">
          Finding Detail
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-8 items-start">
        <div className="flex-1 space-y-4 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <SeverityBadge severity={finding.severity} />
            <span className="text-textmut uppercase tracking-[0.18em] text-[10px] font-bold border border-bordercolor px-2 py-1 rounded bg-surface">{finding.type}</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-black text-textpri tracking-tighter leading-[1.05]">{finding.title}</h1>
          <p className="text-textmut text-lg leading-relaxed">{finding.technical_impact}</p>
        </div>
        <div className={`shrink-0 glass rounded-2xl p-7 flex flex-col items-center gap-3 ${severityGlow}`}>
          <div className="text-[10px] uppercase font-bold text-textmut tracking-[0.25em]">Final Risk Score</div>
          <RiskScore score={finding.final_risk_score} size={176} />
          <div className="w-full pt-3 border-t border-white/[0.06]">
            <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.15em] font-bold text-textmut mb-1.5">
              <span>Confidence</span>
              <span className="font-mono text-textpri">{(finding.confidence * 100).toFixed(0)}%</span>
            </div>
            <div className="h-1.5 w-full bg-background/80 rounded-full overflow-hidden">
              <div className="h-full bg-accent rounded-full" style={{ width: `${finding.confidence * 100}%` }} />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
        <div className="space-y-6">
          <ReasoningBreakdown breakdown={finding.reasoning_breakdown} />
          
          <div className="glass rounded-xl overflow-hidden">
            <div className="bg-surface/60 px-4 py-3 border-b border-white/[0.06] font-bold uppercase tracking-[0.12em] text-xs text-textpri flex items-center gap-2">
              <Activity size={18} className="text-accent" /> Business Impact
            </div>
            <div className="p-4 text-textpri text-sm">
              {finding.business_impact}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass rounded-xl overflow-hidden flex flex-col h-full">
            <div className="bg-surface/60 px-4 py-3 border-b border-white/[0.06] flex justify-between items-center">
              <div className="font-bold uppercase tracking-[0.12em] text-xs text-textpri flex items-center gap-2">
                <GraduationCap size={18} className="text-accent" /> Targeted Guidance
              </div>
            </div>
            <div className="p-4 border-b border-bordercolor bg-surface/30">
              <AudienceSelector selected={audience} onChange={setAudience} />
            </div>
            <div className="p-4 text-textpri text-sm leading-relaxed whitespace-pre-wrap flex-1">
              {finding.audience_guidance?.[audience] || <span className="text-textmut italic">No guidance available for this persona.</span>}
            </div>
          </div>
        </div>
      </div>

      {(finding.recommended_actions?.length > 0 || finding.learning_resources?.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {finding.recommended_actions?.length > 0 && (
            <div className="glass rounded-xl p-5">
              <h3 className="font-bold uppercase tracking-[0.12em] text-xs text-textpri mb-3 flex items-center gap-2"><ShieldAlert size={18} className="text-success" /> Recommended Actions</h3>
              <ul className="space-y-2">
                {finding.recommended_actions.map((act, i) => (
                  <li key={i} className="text-sm text-textmut flex gap-2"><span className="text-success">▹</span> {act}</li>
                ))}
              </ul>
            </div>
          )}
          {finding.learning_resources?.length > 0 && (
            <div className="glass rounded-xl p-5">
              <h3 className="font-bold uppercase tracking-[0.12em] text-xs text-textpri mb-3 flex items-center gap-2"><Server size={18} className="text-accent" /> Learning Resources</h3>
              <ul className="space-y-2">
                {finding.learning_resources.map((res, i) => (
                  <li key={i} className="text-sm text-accent hover:underline flex gap-2"><span className="text-textmut">▹</span> <a href={res} target="_blank" rel="noreferrer">{res}</a></li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="bg-surface border border-bordercolor rounded-lg overflow-hidden">
        <button 
          onClick={() => setRawOpen(!rawOpen)}
          className="w-full px-4 py-3 flex justify-between items-center font-semibold text-textmut hover:text-textpri transition-colors"
        >
          Raw Scanner Output
          {rawOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
        {rawOpen && (
          <div className="p-4 border-t border-bordercolor bg-[#0a0f1a] overflow-x-auto">
            <pre className="text-xs text-textmut font-mono">
              {JSON.stringify(finding.raw_data, null, 2)}
            </pre>
          </div>
        )}
      </div>

    </div>
  );
}
