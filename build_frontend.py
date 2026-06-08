import os

files = {
    "frontend/tailwind.config.js": """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0f1a",
        surface: "#111827",
        card: "#1a2235",
        bordercolor: "#1e2d40",
        accent: "#00d4ff",
        danger: "#ff4444",
        warning: "#ffaa00",
        success: "#00ff88",
        textpri: "#e2e8f0",
        textmut: "#64748b",
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', '"Liberation Mono"', '"Courier New"', 'monospace'],
      }
    },
  },
  plugins: [],
}
""",
    "frontend/src/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-background text-textpri font-sans m-0 p-0;
}

/* Custom scrollbar for dark theme */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: #0a0f1a;
}
::-webkit-scrollbar-thumb {
  background: #1e2d40;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}
""",
    "frontend/src/main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
    "frontend/src/App.jsx": """import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import NewScan from './pages/NewScan';
import ScanDetail from './pages/ScanDetail';
import FindingDetail from './pages/FindingDetail';
import Intelligence from './pages/Intelligence';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scan/new" element={<NewScan />} />
          <Route path="/scan/:scan_id" element={<ScanDetail />} />
          <Route path="/scan/:scan_id/finding/:finding_id" element={<FindingDetail />} />
          <Route path="/intelligence" element={<Intelligence />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
""",
    "frontend/src/api/client.js": """import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default client;
""",
    "frontend/src/components/Layout.jsx": """import React from 'react';
import Sidebar from './Sidebar';

export default function Layout({ children }) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-surface border-b border-bordercolor flex items-center px-6 shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="text-accent font-bold text-xl tracking-wider uppercase">Argus Sentinel</h1>
            <span className="text-textmut text-sm hidden sm:inline">| AI Cybersecurity Reasoning Engine</span>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
""",
    "frontend/src/components/Sidebar.jsx": """import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Target, BookOpen } from 'lucide-react';

export default function Sidebar() {
  const links = [
    { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} /> },
    { name: 'New Scan', path: '/scan/new', icon: <Target size={20} /> },
    { name: 'Intelligence Library', path: '/intelligence', icon: <BookOpen size={20} /> },
  ];

  return (
    <div className="w-60 bg-surface border-r border-bordercolor flex flex-col justify-between shrink-0 h-full">
      <div className="p-4">
        <div className="mb-8 px-2 pt-2">
          <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center mb-2">
            <span className="text-accent font-bold text-xl">A</span>
          </div>
        </div>
        <nav className="space-y-2">
          {links.map((link) => (
            <NavLink
              key={link.name}
              to={link.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                  isActive 
                    ? 'bg-accent/10 text-accent font-medium' 
                    : 'text-textmut hover:bg-card hover:text-textpri'
                }`
              }
            >
              {link.icon}
              {link.name}
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="p-4 border-t border-bordercolor">
        <div className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-mono bg-card text-textmut border border-bordercolor">
          v1.0.0
        </div>
      </div>
    </div>
  );
}
""",
    "frontend/src/components/SeverityBadge.jsx": """import React from 'react';

export default function SeverityBadge({ severity }) {
  const s = (severity || 'informational').toLowerCase();
  let colorClass = 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  
  if (s === 'critical') colorClass = 'bg-danger/20 text-danger border-danger/30';
  else if (s === 'high') colorClass = 'bg-[#ff6b00]/20 text-[#ff6b00] border-[#ff6b00]/30';
  else if (s === 'medium') colorClass = 'bg-warning/20 text-warning border-warning/30';
  else if (s === 'low') colorClass = 'bg-blue-500/20 text-blue-400 border-blue-500/30';

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase border ${colorClass}`}>
      {s === 'informational' ? 'INFO' : s}
    </span>
  );
}
""",
    "frontend/src/components/RiskScore.jsx": """import React from 'react';

export default function RiskScore({ score }) {
  const s = parseFloat(score || 0);
  let color = '#00ff88'; // green
  if (s >= 8.0) color = '#ff4444'; // red
  else if (s >= 6.0) color = '#ff6b00'; // orange
  else if (s >= 4.0) color = '#ffaa00'; // yellow

  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (s / 10) * circumference;

  return (
    <div className="relative flex items-center justify-center w-24 h-24">
      <svg className="transform -rotate-90 w-24 h-24">
        <circle
          cx="48"
          cy="48"
          r={radius}
          stroke="currentColor"
          strokeWidth="6"
          fill="transparent"
          className="text-bordercolor"
        />
        <circle
          cx="48"
          cy="48"
          r={radius}
          stroke={color}
          strokeWidth="6"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-2xl font-bold font-mono text-textpri" style={{ color }}>{s.toFixed(1)}</span>
        <span className="text-xs text-textmut font-mono">/10</span>
      </div>
    </div>
  );
}
""",
    "frontend/src/components/ReasoningBreakdown.jsx": """import React from 'react';

export default function ReasoningBreakdown({ breakdown }) {
  if (!breakdown || breakdown.length === 0) return null;

  const total = breakdown.reduce((acc, step) => acc + step.modifier, 0);

  return (
    <div className="bg-card border border-bordercolor rounded-lg overflow-hidden">
      <div className="bg-surface px-4 py-3 border-b border-bordercolor">
        <h3 className="text-sm font-semibold text-textpri">Why this risk score?</h3>
      </div>
      <div className="p-4 space-y-3">
        {breakdown.map((step, idx) => {
          const mod = step.modifier;
          const isPos = mod > 0;
          return (
            <div key={idx} className="flex gap-4 items-start text-sm pb-3 border-b border-bordercolor last:border-0 last:pb-0">
              <div className={`w-16 shrink-0 font-mono font-bold ${isPos ? 'text-danger' : mod < 0 ? 'text-success' : 'text-textmut'}`}>
                {mod > 0 ? '+' : ''}{mod.toFixed(1)}
              </div>
              <div>
                <div className="font-semibold text-textpri mb-1">{step.label}</div>
                <div className="text-textmut">{step.reason}</div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="bg-surface/50 px-4 py-3 border-t border-bordercolor flex gap-4 text-sm font-bold">
        <div className="w-16 shrink-0 font-mono text-textpri">{total > 0 ? '+' : ''}{total.toFixed(1)}</div>
        <div className="text-textpri">Total Modifier</div>
      </div>
    </div>
  );
}
""",
    "frontend/src/components/AudienceSelector.jsx": """import React from 'react';

export default function AudienceSelector({ selected, onChange }) {
  const audiences = [
    { id: 'student', label: 'Student' },
    { id: 'developer', label: 'Developer' },
    { id: 'bug_bounty_hunter', label: 'Bug Bounty Hunter' },
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
""",
    "frontend/src/components/LoadingSpinner.jsx": """import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <Loader2 className="animate-spin text-accent" size={32} />
    </div>
  );
}
""",
    "frontend/src/pages/Dashboard.jsx": """import React, { useEffect, useState } from 'react';
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
""",
    "frontend/src/pages/NewScan.jsx": """import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Target } from 'lucide-react';
import client from '../api/client';
import AudienceSelector from '../components/AudienceSelector';

export default function NewScan() {
  const [target, setTarget] = useState('');
  const [audience, setAudience] = useState('student');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!target) {
      setError('Target is required');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const res = await client.post('/scans/', { target, audience });
      navigate(`/scan/${res.data.id}`);
    } catch (err) {
      setError('Failed to launch scan');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-textpri mb-2">Launch New Scan</h2>
        <p className="text-textmut">Enter a target domain or IP address to begin reconnaissance.</p>
      </div>

      <div className="bg-card border border-bordercolor rounded-xl overflow-hidden shadow-lg shadow-black/20">
        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          {error && <div className="bg-danger/20 text-danger border border-danger/30 p-3 rounded-md text-sm">{error}</div>}
          
          <div className="space-y-2">
            <label className="block text-sm font-medium text-textpri">Target Scope</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Target size={18} className="text-textmut" />
              </div>
              <input 
                type="text" 
                value={target}
                onChange={e => setTarget(e.target.value)}
                placeholder="e.g. example.com or 192.168.1.1" 
                className="w-full bg-surface border border-bordercolor rounded-lg pl-10 pr-4 py-3 text-textpri focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all placeholder:text-textmut/50 font-mono"
              />
            </div>
          </div>

          <div className="space-y-3">
            <label className="block text-sm font-medium text-textpri">Select Your Persona</label>
            <p className="text-xs text-textmut mb-2">Argus Sentinel will tailor the guidance and reasoning breakdown to this audience level.</p>
            <AudienceSelector selected={audience} onChange={setAudience} />
          </div>

          <div className="pt-4">
            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-accent text-background font-bold py-3 rounded-lg hover:bg-accent/90 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Shield size={20} />
              {loading ? 'Launching Protocol...' : 'Launch Sentinel Scan'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
""",
    "frontend/src/pages/ScanDetail.jsx": """import React, { useEffect, useState } from 'react';
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
""",
    "frontend/src/pages/FindingDetail.jsx": """import React, { useEffect, useState } from 'react';
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
""",
    "frontend/src/pages/Intelligence.jsx": """import React, { useEffect, useState } from 'react';
import { Search, Server, Code, ShieldAlert, ChevronDown, ChevronUp } from 'lucide-react';
import client from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import SeverityBadge from '../components/SeverityBadge';

const EntryCard = ({ entry, type }) => {
  const [expanded, setExpanded] = useState(false);
  const name = entry.service || entry.technology || entry.vulnerability;
  
  return (
    <div className="bg-card border border-bordercolor rounded-lg overflow-hidden transition-all">
      <div 
        className="p-4 cursor-pointer hover:bg-surface/50 flex justify-between items-start"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h3 className="font-bold text-textpri text-lg">{name}</h3>
            {entry.risk_level && <SeverityBadge severity={entry.risk_level} />}
            {entry.port && <span className="text-xs font-mono bg-surface border border-bordercolor px-2 py-0.5 rounded text-textmut">Port {entry.port}</span>}
          </div>
          <p className={`text-sm text-textmut ${expanded ? '' : 'line-clamp-2'}`}>{entry.description}</p>
        </div>
        <div className="text-textmut mt-1">
          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </div>
      </div>
      
      {expanded && (
        <div className="p-4 border-t border-bordercolor bg-surface/30 space-y-4">
          {entry.common_risks && (
            <div>
              <div className="text-xs font-bold text-textpri uppercase tracking-wider mb-2">Common Risks</div>
              <ul className="text-sm text-textmut list-disc list-inside space-y-1">
                {entry.common_risks.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
          {entry.misconfigurations && (
            <div>
              <div className="text-xs font-bold text-textpri uppercase tracking-wider mb-2">Misconfigurations</div>
              <ul className="text-sm text-textmut list-disc list-inside space-y-1">
                {entry.misconfigurations.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
          {entry.audience_guidance && (
            <div>
              <div className="text-xs font-bold text-textpri uppercase tracking-wider mb-2">Student Guidance</div>
              <p className="text-sm text-textmut whitespace-pre-wrap">{entry.audience_guidance.student}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default function Intelligence() {
  const [data, setData] = useState({ services: {}, technologies: {}, vulnerabilities: {} });
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('services');
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState(null);

  useEffect(() => {
    Promise.all([
      client.get('/intelligence/services'),
      client.get('/intelligence/technologies'),
      client.get('/intelligence/vulnerabilities')
    ]).then(([s, t, v]) => {
      setData({
        services: s.data,
        technologies: t.data,
        vulnerabilities: v.data
      });
      setLoading(false);
    }).catch(err => setLoading(false));
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!search.trim()) {
      setSearchResults(null);
      return;
    }
    setLoading(true);
    try {
      const res = await client.get(`/intelligence/search?q=${search}`);
      setSearchResults(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data.services) return <LoadingSpinner />;

  const currentData = searchResults 
    ? searchResults 
    : Object.values(data[tab] || {});

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-textpri">Intelligence Library</h2>
          <p className="text-textmut text-sm mt-1">The core knowledge base powering Argus Sentinel's deterministic reasoning.</p>
        </div>
        
        <form onSubmit={handleSearch} className="relative w-full md:w-72">
          <input 
            type="text" 
            value={search}
            onChange={e => {
              setSearch(e.target.value);
              if (!e.target.value) setSearchResults(null);
            }}
            placeholder="Search KB..." 
            className="w-full bg-card border border-bordercolor rounded-md pl-10 pr-4 py-2 text-sm text-textpri focus:outline-none focus:border-accent transition-colors"
          />
          <Search size={16} className="absolute left-3 top-2.5 text-textmut" />
        </form>
      </div>

      {!searchResults && (
        <div className="flex border-b border-bordercolor space-x-6">
          <button 
            onClick={() => setTab('services')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${tab === 'services' ? 'border-accent text-accent' : 'border-transparent text-textmut hover:text-textpri'}`}
          ><Server size={16} /> Services</button>
          <button 
            onClick={() => setTab('technologies')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${tab === 'technologies' ? 'border-accent text-accent' : 'border-transparent text-textmut hover:text-textpri'}`}
          ><Code size={16} /> Technologies</button>
          <button 
            onClick={() => setTab('vulnerabilities')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${tab === 'vulnerabilities' ? 'border-accent text-accent' : 'border-transparent text-textmut hover:text-textpri'}`}
          ><ShieldAlert size={16} /> Vulnerabilities</button>
        </div>
      )}

      {searchResults && (
        <div className="text-sm text-textmut mb-4">
          Found {searchResults.length} results for "{search}"
          <button onClick={() => {setSearch(''); setSearchResults(null);}} className="ml-4 text-accent hover:underline">Clear Search</button>
        </div>
      )}

      <div className="space-y-4">
        {searchResults ? (
          searchResults.map((item, i) => (
            <EntryCard key={i} entry={item.entry} type={item.type} />
          ))
        ) : (
          currentData.map((item, i) => (
            <EntryCard key={i} entry={item} type={tab} />
          ))
        )}
        
        {currentData.length === 0 && (
          <div className="text-center p-12 text-textmut bg-card border border-bordercolor rounded-lg">
            No entries found.
          </div>
        )}
      </div>
    </div>
  );
}
"""
}

for filepath, content in files.items():
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Frontend React components built.")
