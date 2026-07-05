import React, { useState } from 'react';
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
    if (!target || loading) {
      if (!target) setError('Target is required');
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
