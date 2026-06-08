import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Server, Activity, ShieldAlert, GraduationCap, ChevronDown, ChevronUp } from 'lucide-react';
import client from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import SeverityBadge from '../components/SeverityBadge';
import RiskScore from '../components/RiskScore';
import ReasoningBreakdown from '../components/ReasoningBreakdown';
import AudienceSelector from '../components/AudienceSelector';

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

  if (loading) return <LoadingSpinner />;
  if (!finding) return <div className="text-danger">Finding not found</div>;

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
        <div className="flex-1 space-y-4">
          <div className="flex items-center gap-3">
            <SeverityBadge severity={finding.severity} />
            <span className="text-textmut uppercase tracking-wider text-xs font-bold border border-bordercolor px-2 py-0.5 rounded bg-surface">{finding.type}</span>
          </div>
          <h1 className="text-3xl font-bold text-textpri">{finding.title}</h1>
          <p className="text-textmut text-lg">{finding.technical_impact}</p>
        </div>
        <div className="shrink-0 bg-card border border-bordercolor rounded-xl p-6 flex flex-col items-center gap-2">
          <div className="text-xs uppercase font-bold text-textmut tracking-wider">Final Risk Score</div>
          <RiskScore score={finding.final_risk_score} />
          <div className="text-xs text-textmut mt-2">Confidence: {(finding.confidence * 100).toFixed(0)}%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
        <div className="space-y-6">
          <ReasoningBreakdown breakdown={finding.reasoning_breakdown} />
          
          <div className="bg-card border border-bordercolor rounded-lg overflow-hidden">
            <div className="bg-surface px-4 py-3 border-b border-bordercolor font-semibold flex items-center gap-2">
              <Activity size={18} className="text-accent" /> Business Impact
            </div>
            <div className="p-4 text-textpri text-sm">
              {finding.business_impact}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-card border border-bordercolor rounded-lg overflow-hidden flex flex-col h-full">
            <div className="bg-surface px-4 py-3 border-b border-bordercolor flex justify-between items-center">
              <div className="font-semibold flex items-center gap-2">
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
            <div className="bg-card border border-bordercolor rounded-lg p-5">
              <h3 className="font-semibold text-textpri mb-3 flex items-center gap-2"><ShieldAlert size={18} className="text-success" /> Recommended Actions</h3>
              <ul className="space-y-2">
                {finding.recommended_actions.map((act, i) => (
                  <li key={i} className="text-sm text-textmut flex gap-2"><span className="text-success">▹</span> {act}</li>
                ))}
              </ul>
            </div>
          )}
          {finding.learning_resources?.length > 0 && (
            <div className="bg-card border border-bordercolor rounded-lg p-5">
              <h3 className="font-semibold text-textpri mb-3 flex items-center gap-2"><Server size={18} className="text-accent" /> Learning Resources</h3>
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
