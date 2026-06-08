import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertTriangle, AlertCircle, Info, ArrowRight } from 'lucide-react';
import client from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import SeverityBadge from '../components/SeverityBadge';

export default function ScanDetail() {
  const { scan_id } = useParams();
  const [summary, setSummary] = useState(null);
  const [findings, setFindings] = useState([]);
  const [status, setStatus] = useState('pending');
  const [loading, setLoading] = useState(true);

  const fetchScan = async () => {
    try {
      const sumRes = await client.get(`/findings/scan/${scan_id}/summary`);
      setSummary(sumRes.data);
      setStatus(sumRes.data.status || 'completed'); // Status comes from scan /status endpoint actually, but summary might not have it. Let's fetch status too.
      
      const statRes = await client.get(`/scans/${scan_id}/status`);
      setStatus(statRes.data.status);

      if (statRes.data.status === 'completed' || statRes.data.status === 'failed') {
        const findRes = await client.get(`/findings/scan/${scan_id}`);
        setFindings(findRes.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScan();
    const interval = setInterval(() => {
      if (status === 'pending' || status === 'running') {
        fetchScan();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [scan_id, status]);

  if (loading && !summary) return <LoadingSpinner />;
  if (!summary) return <div className="text-danger">Scan not found</div>;

  const isRunning = status === 'pending' || status === 'running';

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center gap-4 border-b border-bordercolor pb-4">
        <Link to="/" className="p-2 hover:bg-card rounded-md text-textmut hover:text-textpri transition-colors">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-textpri font-mono">{summary.target}</h2>
            <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold uppercase border
              ${isRunning ? 'bg-warning/20 text-warning border-warning/30 animate-pulse' : ''}
              ${status === 'failed' ? 'bg-danger/20 text-danger border-danger/30' : ''}
              ${status === 'completed' ? 'bg-success/20 text-success border-success/30' : ''}
            `}>
              {status}
            </span>
          </div>
          <p className="text-sm text-textmut mt-1">Audience profile: <span className="text-textpri capitalize">{summary.audience.replace('_', ' ')}</span></p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <div className="col-span-2 bg-card border border-bordercolor rounded-lg p-4">
          <div className="text-textmut text-xs uppercase font-bold tracking-wider mb-1">Combined Risk</div>
          <div className="text-xl font-bold flex items-center gap-2">
            <SeverityBadge severity={summary.combined_risk_level} />
          </div>
        </div>
        <div className="bg-card border border-danger/30 rounded-lg p-4">
          <div className="text-danger text-xs uppercase font-bold tracking-wider mb-1">Critical</div>
          <div className="text-2xl font-bold text-textpri">{summary.by_severity.critical}</div>
        </div>
        <div className="bg-card border border-[#ff6b00]/30 rounded-lg p-4">
          <div className="text-[#ff6b00] text-xs uppercase font-bold tracking-wider mb-1">High</div>
          <div className="text-2xl font-bold text-textpri">{summary.by_severity.high}</div>
        </div>
        <div className="bg-card border border-warning/30 rounded-lg p-4">
          <div className="text-warning text-xs uppercase font-bold tracking-wider mb-1">Medium</div>
          <div className="text-2xl font-bold text-textpri">{summary.by_severity.medium}</div>
        </div>
        <div className="bg-card border border-bordercolor rounded-lg p-4">
          <div className="text-blue-400 text-xs uppercase font-bold tracking-wider mb-1">Low</div>
          <div className="text-2xl font-bold text-textpri">{summary.by_severity.low}</div>
        </div>
      </div>

      <div>
        <h3 className="text-xl font-bold text-textpri mb-4">Findings</h3>
        
        {isRunning ? (
          <div className="bg-card border border-bordercolor rounded-lg p-12 text-center flex flex-col items-center">
            <Loader2 className="animate-spin text-accent mb-4" size={32} />
            <h4 className="text-lg font-medium text-textpri">Scan in Progress</h4>
            <p className="text-textmut mt-2 max-w-md">Argus Sentinel is actively reasoning over the attack surface. Findings will appear once the scan completes.</p>
          </div>
        ) : findings.length === 0 ? (
          <div className="bg-card border border-bordercolor rounded-lg p-12 text-center">
            <div className="text-textmut">No findings discovered.</div>
          </div>
        ) : (
          <div className="bg-card border border-bordercolor rounded-lg overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-surface text-textmut border-b border-bordercolor">
                <tr>
                  <th className="px-6 py-3 font-semibold">Severity</th>
                  <th className="px-6 py-3 font-semibold">Type</th>
                  <th className="px-6 py-3 font-semibold w-full">Finding</th>
                  <th className="px-6 py-3 font-semibold">Risk Score</th>
                  <th className="px-6 py-3 font-semibold"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-bordercolor">
                {findings.map(f => (
                  <tr key={f.id} className="hover:bg-surface/50 transition-colors">
                    <td className="px-6 py-4"><SeverityBadge severity={f.severity} /></td>
                    <td className="px-6 py-4 text-textmut uppercase tracking-wider text-xs font-bold">{f.type}</td>
                    <td className="px-6 py-4 font-medium text-textpri">{f.title}</td>
                    <td className="px-6 py-4 font-mono font-bold">{f.final_risk_score.toFixed(1)}</td>
                    <td className="px-6 py-4 text-right">
                      <Link to={`/scan/${scan_id}/finding/${f.id}`} className="text-accent hover:underline text-sm font-medium">
                        Analyze
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
