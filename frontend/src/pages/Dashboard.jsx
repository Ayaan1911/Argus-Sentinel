import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Target, Activity, ShieldAlert, ArrowRight } from 'lucide-react';
import client from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Dashboard() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get('/scans/')
      .then(res => {
        setScans(res.data);
        setLoading(false);
      })
      .catch(err => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  const totalScans = scans.length;
  const totalFindings = scans.reduce((acc, s) => acc + s.finding_count, 0);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-textpri">Dashboard Overview</h2>
        <Link to="/scan/new" className="bg-accent text-background px-4 py-2 rounded-md font-semibold hover:bg-accent/90 transition-colors flex items-center gap-2">
          <Target size={18} /> New Scan
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-card border border-bordercolor rounded-lg p-6 flex items-center gap-4">
          <div className="p-3 bg-blue-500/20 text-blue-400 rounded-lg"><Activity size={24} /></div>
          <div>
            <div className="text-3xl font-bold text-textpri">{totalScans}</div>
            <div className="text-sm text-textmut uppercase tracking-wider font-semibold">Total Scans</div>
          </div>
        </div>
        <div className="bg-card border border-bordercolor rounded-lg p-6 flex items-center gap-4">
          <div className="p-3 bg-danger/20 text-danger rounded-lg"><ShieldAlert size={24} /></div>
          <div>
            <div className="text-3xl font-bold text-textpri">{totalFindings}</div>
            <div className="text-sm text-textmut uppercase tracking-wider font-semibold">Total Findings</div>
          </div>
        </div>
      </div>

      <h3 className="text-xl font-bold text-textpri pt-4">Recent Scans</h3>
      {scans.length === 0 ? (
        <div className="bg-card border border-bordercolor rounded-lg p-12 text-center">
          <div className="text-textmut mb-4">No scans yet.</div>
          <Link to="/scan/new" className="text-accent hover:underline inline-flex items-center gap-1">
            Start your first scan <ArrowRight size={16} />
          </Link>
        </div>
      ) : (
        <div className="bg-card border border-bordercolor rounded-lg overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-surface text-textmut">
              <tr>
                <th className="px-6 py-3 font-semibold">Target</th>
                <th className="px-6 py-3 font-semibold">Status</th>
                <th className="px-6 py-3 font-semibold">Findings</th>
                <th className="px-6 py-3 font-semibold">Date</th>
                <th className="px-6 py-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-bordercolor">
              {scans.map(scan => {
                const isRunning = scan.status === 'running';
                const isPending = scan.status === 'pending';
                const isFailed = scan.status === 'failed';
                return (
                  <tr key={scan.id} className="hover:bg-surface/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-textpri">{scan.target}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold uppercase border
                        ${isRunning ? 'bg-warning/20 text-warning border-warning/30 animate-pulse' : ''}
                        ${isPending ? 'bg-gray-500/20 text-gray-400 border-gray-500/30' : ''}
                        ${isFailed ? 'bg-danger/20 text-danger border-danger/30' : ''}
                        ${scan.status === 'completed' ? 'bg-success/20 text-success border-success/30' : ''}
                      `}>
                        {scan.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-textmut font-mono">{scan.finding_count}</td>
                    <td className="px-6 py-4 text-textmut">{new Date(scan.created_at).toLocaleString()}</td>
                    <td className="px-6 py-4">
                      <Link to={`/scan/${scan.id}`} className="text-accent hover:text-accent/80 font-medium flex items-center gap-1">
                        View <ArrowRight size={14} />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
