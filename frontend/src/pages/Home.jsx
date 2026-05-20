import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { createScan, listScans, deleteScan } from '../api/client'
import StatusBadge from '../components/StatusBadge'

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatRelativeTime(dateStr) {
  if (!dateStr) return '—'
  const date = new Date(dateStr)
  if (isNaN(date)) return '—'
  const diffMs = Date.now() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  return `${diffDay}d ago`
}

function validateDomain(domain) {
  if (!domain) return 'Domain is required.'
  const trimmed = domain.trim()
  // Strip protocol if user accidentally adds it
  const stripped = trimmed.replace(/^https?:\/\//i, '').replace(/\/.*$/, '')
  // Simple domain regex
  if (!/^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)*\.[a-z]{2,}$/i.test(stripped)) {
    return 'Enter a valid domain (e.g. example.com).'
  }
  return null
}

// ── Eye/Radar SVG Logo ────────────────────────────────────────────────────────

function ArgusLogo() {
  return (
    <svg
      viewBox="0 0 120 120"
      width="88"
      height="88"
      className="mx-auto mb-4 drop-shadow-[0_0_24px_rgba(0,255,136,0.6)]"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Outer ring */}
      <circle cx="60" cy="60" r="54" stroke="#00ff88" strokeWidth="1.5" strokeDasharray="4 3" opacity="0.4" />
      {/* Mid ring */}
      <circle cx="60" cy="60" r="40" stroke="#00ff88" strokeWidth="1" opacity="0.35" />
      {/* Inner ring */}
      <circle cx="60" cy="60" r="26" stroke="#00ff88" strokeWidth="1.5" opacity="0.6" />
      {/* Crosshairs */}
      <line x1="60" y1="6" x2="60" y2="34" stroke="#00ff88" strokeWidth="1.5" opacity="0.5" />
      <line x1="60" y1="86" x2="60" y2="114" stroke="#00ff88" strokeWidth="1.5" opacity="0.5" />
      <line x1="6" y1="60" x2="34" y2="60" stroke="#00ff88" strokeWidth="1.5" opacity="0.5" />
      <line x1="86" y1="60" x2="114" y2="60" stroke="#00ff88" strokeWidth="1.5" opacity="0.5" />
      {/* Diagonal ticks */}
      <line x1="21" y1="21" x2="30" y2="30" stroke="#00ff88" strokeWidth="1" opacity="0.3" />
      <line x1="99" y1="21" x2="90" y2="30" stroke="#00ff88" strokeWidth="1" opacity="0.3" />
      <line x1="21" y1="99" x2="30" y2="90" stroke="#00ff88" strokeWidth="1" opacity="0.3" />
      <line x1="99" y1="99" x2="90" y2="90" stroke="#00ff88" strokeWidth="1" opacity="0.3" />
      {/* Eye whites */}
      <ellipse cx="60" cy="60" rx="20" ry="12" fill="#0a1a12" stroke="#00ff88" strokeWidth="1.5" opacity="0.9" />
      {/* Iris */}
      <circle cx="60" cy="60" r="8" fill="#00ff88" opacity="0.15" stroke="#00ff88" strokeWidth="1.5" />
      {/* Pupil */}
      <circle cx="60" cy="60" r="4" fill="#00ff88" opacity="0.9" />
      {/* Pupil glow */}
      <circle cx="60" cy="60" r="4" fill="#00ff88">
        <animate attributeName="opacity" values="0.9;0.4;0.9" dur="2s" repeatCount="indefinite" />
        <animate attributeName="r" values="4;5;4" dur="2s" repeatCount="indefinite" />
      </circle>
      {/* Radar sweep line */}
      <line x1="60" y1="60" x2="60" y2="20" stroke="#00ff88" strokeWidth="1.5" opacity="0.7" strokeLinecap="round">
        <animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="4s" repeatCount="indefinite" />
      </line>
    </svg>
  )
}

// ── Disclaimer Banner ─────────────────────────────────────────────────────────

function DisclaimerBanner() {
  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-[#1a1200] border-b border-[#ffcc0033] px-4 py-2 text-center">
      <p className="text-[0.7rem] text-[#ffcc00] font-medium tracking-wide">
        ⚠️ For authorized use only. Only scan domains you own or have explicit permission to test.
      </p>
    </div>
  )
}

// ── Main Home Component ───────────────────────────────────────────────────────

export default function Home() {
  const navigate = useNavigate()

  const [domain, setDomain]         = useState('')
  const [scans, setScans]           = useState([])
  const [loading, setLoading]       = useState(false)
  const [scanError, setScanError]   = useState(null)
  const [validationErr, setValidationErr] = useState(null)
  const [deleteId, setDeleteId]     = useState(null) // id pending confirm
  const [scansLoading, setScansLoading] = useState(true)

  // ── Fetch scans ────────────────────────────────────────────────────────────

  const fetchScans = useCallback(async () => {
    try {
      const data = await listScans()
      setScans(Array.isArray(data) ? data : [])
    } catch {
      // silently handle — show empty table
    } finally {
      setScansLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchScans()
    const interval = setInterval(fetchScans, 5000)
    return () => clearInterval(interval)
  }, [fetchScans])

  // ── Submit ─────────────────────────────────────────────────────────────────

  async function handleSubmit(e) {
    e.preventDefault()
    const trimmed = domain.trim().replace(/^https?:\/\//i, '').replace(/\/.*$/, '')
    const err = validateDomain(trimmed)
    if (err) {
      setValidationErr(err)
      return
    }
    setValidationErr(null)
    setScanError(null)
    setLoading(true)
    try {
      const result = await createScan(trimmed)
      const id = result?.id ?? result?.scan_id ?? result?._id
      if (id) {
        navigate(`/scan/${id}`)
      } else {
        setScanError('Scan created but no ID returned. Check the console.')
      }
    } catch (ex) {
      setScanError(
        ex?.response?.data?.error
          || ex?.response?.data?.message
          || ex?.message
          || 'Failed to start scan.'
      )
    } finally {
      setLoading(false)
    }
  }

  // ── Delete ─────────────────────────────────────────────────────────────────

  async function handleDelete(id) {
    if (deleteId !== id) {
      setDeleteId(id)
      return
    }
    setDeleteId(null)
    try {
      await deleteScan(id)
      setScans((prev) => prev.filter((s) => (s.id ?? s._id ?? s.scan_id) !== id))
    } catch {
      // ignore
    }
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  function getScanId(scan) {
    return scan.id ?? scan._id ?? scan.scan_id
  }

  function getSubdomainCount(scan) {
    if (typeof scan.subdomain_count === 'number') return scan.subdomain_count
    if (Array.isArray(scan.subdomains)) return scan.subdomains.length
    return '—'
  }

  function handleDomainChange(e) {
    setDomain(e.target.value)
    if (validationErr) setValidationErr(null)
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <DisclaimerBanner />

      {/* ── Main content ────────────────────────────────────────── */}
      <main className="max-w-5xl mx-auto px-4 pt-20 pb-16">

        {/* ── Hero ──────────────────────────────────────────────── */}
        <section className="text-center py-14 animate-fade-in">
          <ArgusLogo />

          <h1
            className="text-5xl md:text-6xl font-black tracking-[0.15em] uppercase mb-3"
            style={{
              color: '#00ff88',
              textShadow: '0 0 15px rgba(0,255,136,0.7), 0 0 30px rgba(0,255,136,0.4)',
            }}
          >
            ARGUS-SENTINEL
          </h1>

          <p className="text-[#888888] text-lg font-light tracking-wide mb-2">
            A hundred eyes on your attack surface.
          </p>
          <p className="text-[#444444] text-sm font-mono">
            Automated reconnaissance &amp; vulnerability enumeration
          </p>
        </section>

        {/* ── Scan Input ────────────────────────────────────────── */}
        <section className="animate-slide-up max-w-2xl mx-auto mb-16">
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="flex gap-3">
              <div className="relative flex-1">
                {/* Shield icon inside input */}
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#444444] text-lg pointer-events-none select-none">
                  🎯
                </span>
                <input
                  type="text"
                  value={domain}
                  onChange={handleDomainChange}
                  placeholder="Enter target domain (e.g. example.com)"
                  className="input-dark pl-11 text-base h-14"
                  spellCheck={false}
                  autoComplete="off"
                  disabled={loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading || !domain.trim()}
                className="btn-primary px-6 h-14 whitespace-nowrap flex-shrink-0"
              >
                {loading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                    </svg>
                    INITIATING...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 105 11a6 6 0 0012 0z" />
                    </svg>
                    INITIATE SCAN
                  </>
                )}
              </button>
            </div>

            {/* Validation error */}
            {validationErr && (
              <p className="text-[#ff4444] text-sm flex items-center gap-2 pl-1">
                <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12A9 9 0 113 12a9 9 0 0118 0z" />
                </svg>
                {validationErr}
              </p>
            )}

            {/* API error */}
            {scanError && (
              <div className="rounded-lg border border-[rgba(255,68,68,0.3)] bg-[#150a0a] p-3 text-sm text-[#ff4444] flex items-start gap-2">
                <span className="flex-shrink-0 mt-0.5">✕</span>
                <span>{scanError}</span>
              </div>
            )}

            <p className="text-[#444444] text-xs text-center pt-1">
              Enter a bare domain only — no protocol or path required
            </p>
          </form>
        </section>

        {/* ── Recent Scans ──────────────────────────────────────── */}
        <section className="animate-slide-up" style={{ animationDelay: '0.1s' }}>
          {/* Section heading */}
          <div className="flex items-center gap-3 mb-6">
            <h2 className="text-xs font-bold tracking-[0.2em] uppercase text-[#00ff88]">
              Recent Scans
            </h2>
            <div className="flex-1 h-px bg-gradient-to-r from-[#00ff88] to-transparent opacity-30" />
            {!scansLoading && (
              <span className="text-[#444444] text-xs font-mono">{scans.length} total</span>
            )}
          </div>

          <div className="card overflow-hidden">
            {scansLoading ? (
              /* Loading skeleton */
              <div className="p-8 space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex gap-4 animate-pulse">
                    <div className="h-4 bg-[#1e1e1e] rounded flex-1" />
                    <div className="h-4 bg-[#1e1e1e] rounded w-20" />
                    <div className="h-4 bg-[#1e1e1e] rounded w-16" />
                    <div className="h-4 bg-[#1e1e1e] rounded w-24" />
                  </div>
                ))}
              </div>
            ) : scans.length === 0 ? (
              /* Empty state */
              <div className="py-16 text-center">
                <div className="text-5xl mb-4 opacity-30">🔭</div>
                <p className="text-[#555555] text-sm">No scans yet.</p>
                <p className="text-[#444444] text-xs mt-1">Enter a domain above to begin reconnaissance.</p>
              </div>
            ) : (
              /* Scans table */
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Domain</th>
                      <th>Status</th>
                      <th>Subdomains</th>
                      <th>Created</th>
                      <th className="text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scans.map((scan) => {
                      const id = getScanId(scan)
                      const isPendingDelete = deleteId === id
                      return (
                        <tr key={id} className={isPendingDelete ? 'bg-[rgba(255,68,68,0.05)]' : ''}>
                          {/* Domain */}
                          <td>
                            <button
                              onClick={() => navigate(`/scan/${id}`)}
                              className="font-mono text-[#e5e5e5] hover:text-[#00ff88] transition-colors text-sm tracking-wide"
                            >
                              {scan.domain || scan.target}
                            </button>
                          </td>
                          {/* Status */}
                          <td>
                            <StatusBadge status={scan.status} dot />
                          </td>
                          {/* Subdomains */}
                          <td className="font-mono text-[#888888] text-sm">
                            {getSubdomainCount(scan)}
                          </td>
                          {/* Created */}
                          <td className="text-[#555555] text-xs font-mono">
                            {formatRelativeTime(scan.created_at ?? scan.createdAt)}
                          </td>
                          {/* Actions */}
                          <td className="text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => navigate(`/scan/${id}`)}
                                className="btn-ghost text-xs py-1.5 px-3"
                              >
                                VIEW →
                              </button>
                              <button
                                onClick={() => handleDelete(id)}
                                className={`btn-danger text-xs py-1.5 px-3 ${
                                  isPendingDelete ? '!bg-[rgba(255,68,68,0.15)] !border-[#ff4444]' : ''
                                }`}
                              >
                                {isPendingDelete ? 'CONFIRM' : 'DELETE'}
                              </button>
                              {isPendingDelete && (
                                <button
                                  onClick={() => setDeleteId(null)}
                                  className="text-[#555555] hover:text-[#aaa] text-xs px-2 py-1.5 transition-colors"
                                >
                                  Cancel
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        {/* ── Footer ────────────────────────────────────────────── */}
        <footer className="mt-16 text-center text-[#333333] text-xs font-mono">
          <p>ARGUS-SENTINEL v1.0.0 — Operate responsibly.</p>
        </footer>
      </main>
    </div>
  )
}
