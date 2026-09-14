import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Target, Activity, ShieldAlert, ArrowRight } from 'lucide-react';
import client from '../api/client';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line, LabelList } from 'recharts';
import StatusPill from '../components/StatusPill';
import { SEVERITY_COLORS, TYPE_COLORS, CHART_NEUTRAL, STATE_COLORS } from '../theme';

const COLORS = SEVERITY_COLORS;

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card border border-bordercolor p-2 rounded shadow-lg text-sm text-textpri">
        <p className="font-semibold">{payload[0].name || payload[0].payload.name || payload[0].payload.date}</p>
        <p className="font-mono">{payload[0].value} findings</p>
      </div>
    );
  }
  return null;
};

const ScansTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card border border-bordercolor p-2 rounded shadow-lg text-sm text-textpri">
        <p className="font-semibold">{payload[0].payload.date}</p>
        <p className="font-mono">{payload[0].value} scans</p>
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [scans, setScans] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      client.get('/scans/'),
      client.get('/scans/dashboard-stats')
    ])
      .then(([scansRes, statsRes]) => {
        setScans(scansRes.data);
        setStats(statsRes.data);
        setLoading(false);
      })
      .catch(err => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 max-w-6xl mx-auto animate-pulse">
        <div className="flex justify-between items-center"><div className="h-8 w-48 bg-surface rounded"></div></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-28 bg-surface rounded-lg"></div>
          <div className="h-28 bg-surface rounded-lg"></div>
          <div className="h-28 bg-surface rounded-lg"></div>
        </div>
        <div className="h-64 bg-surface rounded-lg"></div>
        <div className="h-64 bg-surface rounded-lg"></div>
      </div>
    );
  }

  const totalScans = scans.length;
  const totalFindings = stats?.total_findings || 0;

  // Prepare chart data
  const severityData = stats ? [
    { name: 'Critical', value: stats.severity_distribution.critical, color: COLORS.critical },
    { name: 'High', value: stats.severity_distribution.high, color: COLORS.high },
    { name: 'Medium', value: stats.severity_distribution.medium, color: COLORS.medium },
    { name: 'Low', value: stats.severity_distribution.low, color: COLORS.low },
    { name: 'Info', value: stats.severity_distribution.info, color: COLORS.info },
  ].filter(d => d.value > 0) : [];

  const typeData = stats ? [
    { name: 'Vulnerability', value: stats.type_breakdown.vulnerability || 0, fill: TYPE_COLORS.vulnerability },
    { name: 'Port', value: stats.type_breakdown.port || 0, fill: TYPE_COLORS.port },
    { name: 'Subdomain', value: stats.type_breakdown.subdomain || 0, fill: TYPE_COLORS.subdomain },
    { name: 'Technology', value: stats.type_breakdown.technology || 0, fill: TYPE_COLORS.technology },
  ].filter(d => d.value > 0).sort((a, b) => b.value - a.value) : [];

  const scansOverTime = stats?.scans_over_time || [];

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-textpri tracking-tight">Dashboard Overview</h2>
        <Link to="/scan/new" className="bg-accent text-background px-4 py-2 rounded-md font-semibold hover:bg-accent/90 transition-colors flex items-center gap-2">
          <Target size={18} /> New Scan
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-card/80 backdrop-blur-md border border-bordercolor rounded-lg p-6 flex items-center gap-4 shadow-lg shadow-black/10">
          <div className="p-3 bg-accent/10 text-accent rounded-lg"><Activity size={24} /></div>
          <div>
            <div className="text-3xl font-bold font-mono text-textpri">{totalScans}</div>
            <div className="text-sm text-textmut uppercase tracking-wider font-semibold">Total Scans</div>
          </div>
        </div>
        <div className="bg-card/80 backdrop-blur-md border border-bordercolor rounded-lg p-6 flex items-center gap-4 shadow-lg shadow-black/10">
          <div className="p-3 bg-accent/10 text-accent rounded-lg"><ShieldAlert size={24} /></div>
          <div>
            <div className="text-3xl font-bold font-mono text-textpri">{totalFindings}</div>
            <div className="text-sm text-textmut uppercase tracking-wider font-semibold">Total Findings</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-card border border-bordercolor rounded-lg p-5 shadow-lg shadow-black/10">
          <h3 className="text-sm text-textmut uppercase tracking-wider font-semibold mb-4">Severity Distribution</h3>
          {severityData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-textmut text-sm">No findings yet</div>
          ) : (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={severityData} innerRadius={50} outerRadius={70} paddingAngle={2} dataKey="value" stroke="none">
                    {severityData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                  </Pie>
                  <RechartsTooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="bg-card border border-bordercolor rounded-lg p-5 shadow-lg shadow-black/10">
          <h3 className="text-sm text-textmut uppercase tracking-wider font-semibold mb-4">Finding Types</h3>
          {typeData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-textmut text-sm">No findings yet</div>
          ) : (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={typeData} layout="vertical" margin={{ top: 0, right: 0, left: 30, bottom: 0 }}>
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: CHART_NEUTRAL.axisText, fontSize: 12 }} />
                  <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: CHART_NEUTRAL.grid }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
                    {typeData.map((entry, index) => (
                      <Cell key={`type-cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="bg-card border border-bordercolor rounded-lg p-5 shadow-lg shadow-black/10">
          <h3 className="text-sm text-textmut uppercase tracking-wider font-semibold mb-4">Scans Over Time (14 Days)</h3>
          {scansOverTime.reduce((a, b) => a + b.count, 0) === 0 ? (
            <div className="h-48 flex items-center justify-center text-textmut text-sm">No scans yet</div>
          ) : (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={scansOverTime} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_NEUTRAL.grid} vertical={false} />
                  <XAxis dataKey="date" hide />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: CHART_NEUTRAL.axisText, fontSize: 12 }} />
                  <RechartsTooltip content={<ScansTooltip />} cursor={{ stroke: CHART_NEUTRAL.grid }} />
                  <Line type="monotone" dataKey="count" stroke={STATE_COLORS.accent} strokeWidth={2} dot={false} activeDot={{ r: 6, fill: STATE_COLORS.accent, stroke: '#0a0e14', strokeWidth: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <h3 className="text-xl font-bold text-textpri tracking-tight pt-4">Recon History</h3>
      {scans.length === 0 ? (
        <div className="bg-card border border-bordercolor rounded-lg p-12 text-center">
          <div className="text-textmut mb-4">No scans yet.</div>
          <Link to="/scan/new" className="text-accent hover:underline inline-flex items-center gap-1">
            Start your first scan <ArrowRight size={16} />
          </Link>
        </div>
      ) : (
        <div className="bg-card border border-bordercolor rounded-lg overflow-hidden shadow-lg shadow-black/10">
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
                return (
                  <tr key={scan.id} className="hover:bg-surface/50 hover:-translate-y-0.5 hover:shadow-lg transition-all group">
                    <td className="px-6 py-4 font-medium text-textpri">{scan.target}</td>
                    <td className="px-6 py-4">
                      <StatusPill status={scan.status} />
                    </td>
                    <td className="px-6 py-4 text-textmut font-mono">{scan.finding_count}</td>
                    <td className="px-6 py-4 text-textmut font-mono">{new Date(scan.created_at).toLocaleString()}</td>
                    <td className="px-6 py-4">
                      <Link to={`/scan/${scan.id}`} className="text-accent hover:text-accent/80 font-medium flex items-center gap-1 opacity-70 group-hover:opacity-100 transition-opacity">
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
