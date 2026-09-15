import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Target, Activity, ShieldAlert, ArrowRight } from 'lucide-react';
import client from '../api/client';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line, LabelList } from 'recharts';
import StatusPill from '../components/StatusPill';
import GlowOrb from '../components/GlowOrb';
import { SEVERITY_COLORS, TYPE_COLORS, CHART_NEUTRAL, STATE_COLORS } from '../theme';

// Severity order, worst first. The hero number is tinted and glowed by the
// worst severity actually present across all scans, so the single biggest
// element on the page answers "how bad is it right now?" before anything is
// read. Only critical/high carry a glow — see tailwind.config.js.
const SEVERITY_RANK = [
  { key: 'critical', label: 'Critical', glow: 'shadow-glow-critical' },
  { key: 'high', label: 'High', glow: 'shadow-glow-high' },
  { key: 'medium', label: 'Medium', glow: '' },
  { key: 'low', label: 'Low', glow: '' },
  { key: 'info', label: 'Info', glow: '' },
];

function dominantSeverity(distribution) {
  if (!distribution) return null;
  return SEVERITY_RANK.find(s => (distribution[s.key] || 0) > 0) || null;
}

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
  const peak = dominantSeverity(stats?.severity_distribution);
  const peakColor = peak ? COLORS[peak.key] : '#f1f5f9';

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
      <div className="flex justify-between items-end gap-4 flex-wrap">
        <div>
          <div className="text-[11px] text-textmut uppercase tracking-[0.25em] font-bold mb-1">Argus Sentinel</div>
          <h2 className="text-4xl sm:text-5xl font-black text-textpri tracking-tighter leading-none">Dashboard</h2>
        </div>
        <Link to="/scan/new" className="bg-accent text-background px-5 py-2.5 rounded-md font-bold hover:bg-accent/90 transition-all shadow-glow-accent flex items-center gap-2 shrink-0">
          <Target size={18} /> New Scan
        </Link>
      </div>
      <div className="h-0.5 w-24 bg-ribbon rounded-full -mt-2" />

      {/* Hero band. One number is deliberately far larger than anything else
          on the page so the dashboard has an unmistakable entry point; its
          color and glow come from the worst severity actually present, which
          is what makes it signal rather than decoration. */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className={`lg:col-span-2 glass rounded-2xl p-6 sm:p-8 ${peak && peak.glow ? peak.glow : ''} ${peak && peak.key === 'critical' ? 'animate-glow-pulse' : ''}`}>
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-2 text-[11px] text-textmut uppercase tracking-[0.25em] font-bold">
                <ShieldAlert size={13} /> Total Findings
              </div>
              <div className="relative mt-3">
                {peak && peak.glow && (
                  <div className="absolute inset-0 flex items-center justify-start -translate-x-8 -translate-y-1/4">
                    <GlowOrb size={200} severity={peakColor} />
                  </div>
                )}
                <div
                  className="relative font-mono font-black tabular-nums tracking-tighter leading-none text-7xl sm:text-8xl"
                  style={{
                    color: peakColor,
                    textShadow: peak && peak.glow ? `0 0 48px ${peakColor}55` : 'none',
                  }}
                >
                  {totalFindings}
                </div>
              </div>
            </div>
            {peak && (
              <div className="text-right">
                <div className="text-[11px] text-textmut uppercase tracking-[0.25em] font-bold">Peak Severity</div>
                <div className="text-2xl sm:text-3xl font-black uppercase tracking-tight mt-2" style={{ color: peakColor }}>
                  {peak.label}
                </div>
              </div>
            )}
          </div>

          {/* The severity distribution as one continuous spectrum bar, so
              proportion is legible before the pie chart below is even read. */}
          {totalFindings > 0 && (
            <>
              <div className="mt-8 h-2.5 w-full flex rounded-full overflow-hidden bg-background/80 ring-1 ring-inset ring-white/[0.05]">
                {SEVERITY_RANK.map(s => {
                  const count = (stats && stats.severity_distribution && stats.severity_distribution[s.key]) || 0;
                  if (count === 0) return null;
                  return (
                    <div
                      key={s.key}
                      title={`${s.label}: ${count}`}
                      style={{
                        width: `${(count / totalFindings) * 100}%`,
                        backgroundColor: COLORS[s.key],
                        boxShadow: s.key === 'critical' ? `0 0 14px ${COLORS.critical}` : 'none',
                      }}
                    />
                  );
                })}
              </div>
              <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2">
                {SEVERITY_RANK.map(s => {
                  const count = (stats && stats.severity_distribution && stats.severity_distribution[s.key]) || 0;
                  const c = COLORS[s.key];
                  return (
                    <div key={s.key} className="flex items-baseline gap-2">
                      <span className="w-1.5 h-1.5 rounded-full shrink-0 self-center" style={{ backgroundColor: c, opacity: count ? 1 : 0.3 }} />
                      <span className="font-mono font-bold tabular-nums text-lg" style={{ color: count ? c : '#475569' }}>{count}</span>
                      <span className="text-[10px] text-textmut uppercase tracking-[0.15em] font-bold">{s.label}</span>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>

        <div className="glass rounded-2xl p-6 sm:p-8 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[11px] text-textmut uppercase tracking-[0.25em] font-bold">
              <Activity size={13} /> Total Scans
            </div>
            <div className="text-6xl font-mono font-black tabular-nums tracking-tighter text-textpri leading-none mt-3">
              {totalScans}
            </div>
          </div>
          <div className="mt-6 pt-4 border-t border-white/[0.06] text-xs text-textmut font-mono">
            {scans.length > 0
              ? <>Last run <span className="text-textpri">{new Date(scans[0].created_at).toLocaleString()}</span></>
              : 'No scans run yet'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass rounded-xl p-5">
          <h3 className="text-[11px] text-textmut uppercase tracking-[0.2em] font-bold mb-4">Severity Distribution</h3>
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

        <div className="glass rounded-xl p-5">
          <h3 className="text-[11px] text-textmut uppercase tracking-[0.2em] font-bold mb-4">Finding Types</h3>
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

        <div className="glass rounded-xl p-5">
          <h3 className="text-[11px] text-textmut uppercase tracking-[0.2em] font-bold mb-4">Scans Over Time (14 Days)</h3>
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

      <h3 className="text-2xl font-bold text-textpri tracking-tight pt-4">Recon <em className="font-serif italic font-normal text-accent">History</em></h3>
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
