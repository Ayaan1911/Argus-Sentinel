import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock } from 'lucide-react';
import client from '../api/client';
import AudienceSelector from '../components/AudienceSelector';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export default function NewScan() {
  const [target, setTarget] = useState(DEMO_MODE ? 'juice-shop' : '');
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
    <div className="editorial-form-page">
      <div className="editorial-page-head">
        <div className="editorial-kicker">Workspace / new investigation</div>
        <h1>Launch a scan.</h1>
        <p>
          {DEMO_MODE
            ? 'This public demo scans the bundled Juice Shop target.'
            : 'Enter a target domain or IP address to begin reconnaissance.'}
        </p>
      </div>

      <div className="editorial-form-panel">
        <form onSubmit={handleSubmit}>
          {error && <div className="editorial-alert" role="alert">{error}</div>}

          <div className="editorial-field">
            {DEMO_MODE
              ? <div className="editorial-field-label">01 / Target scope</div>
              : <label htmlFor="scan-target">01 / Target scope</label>}
            <p>Choose the authorized target for this investigation.</p>
            {DEMO_MODE ? (
              <div className="editorial-locked-target">
                <Lock size={14} aria-hidden="true" /> juice-shop (bundled)
              </div>
            ) : (
              <input id="scan-target" type="text" value={target} onChange={e => setTarget(e.target.value)} placeholder="e.g. example.com or 192.168.1.1" />
            )}
          </div>

          <div className="editorial-field">
            <div className="editorial-field-label">02 / Select your persona</div>
            <p>Argus Sentinel will tailor the guidance and reasoning breakdown to this audience level.</p>
            <AudienceSelector selected={audience} onChange={setAudience} />
          </div>

          <div className="editorial-form-actions">
            <button
              type="submit"
              disabled={loading}
              className="editorial-button"
            >
              {loading ? 'Launching scan…' : (DEMO_MODE ? 'Run demo scan' : 'Launch scan')} <span aria-hidden="true">↗</span>
            </button>
            <span>Subfinder → Httpx → Nmap → Nuclei</span>
          </div>
        </form>
      </div>
    </div>
  );
}
