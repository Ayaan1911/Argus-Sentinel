import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { createScan, listScans, deleteScan } from '../api/client'
import StatusBadge from '../components/StatusBadge'

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatRelativeTime(dateStr) {
  if (!dateStr) return '—'
  const utcDateStr = dateStr.endsWith('Z') ? dateStr : `${dateStr}Z`
  const date = new Date(utcDateStr)
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
  const stripped = trimmed.replace(/^https?:\/\//i, '').replace(/\/.*$/, '')
  if (!/^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)*\.[a-z]{2,}$/i.test(stripped)) {
    return 'Invalid domain format.'
  }
  return null
}

// ── Main Home Component ───────────────────────────────────────────────────────

export default function Home() {
  const navigate = useNavigate()

  const [domain, setDomain]         = useState('')
  const [scans, setScans]           = useState([])
  const [loading, setLoading]       = useState(false)
  const [scanError, setScanError]   = useState(null)
  const [validationErr, setValidationErr] = useState(null)
  const [scansLoading, setScansLoading] = useState(true)

  const fetchScans = useCallback(async () => {
    try {
      const data = await listScans()
      setScans(Array.isArray(data) ? data : [])
      setScansLoading(false)
    } catch (error) {
      console.error('Failed to fetch scans:', error)
      setScansLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchScans()
    const interval = setInterval(fetchScans, 5000)
    return () => clearInterval(interval)
  }, [fetchScans])

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
        setScanError('Failed to get scan ID.')
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

  async function handleDelete(id) {
    if (!window.confirm('Delete this scan?')) return
    try {
      await deleteScan(id)
      setScans((prev) => prev.filter((s) => (s.id ?? s._id ?? s.scan_id) !== id))
    } catch {
    }
  }

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

  return (
    <div className="min-h-screen bg-bg-base">
      
      <header className="border-b border-border bg-bg-surface px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-baseline gap-3">
          <h1 className="text-[14px] font-bold tracking-[0.15em] text-text-primary uppercase">
            Argus Sentinel
          </h1>
          <span className="text-[11px] text-text-muted font-medium">v1.0.0</span>
        </div>
      </header>

      <main className="w-full max-w-7xl mx-auto px-6 py-8">
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Input */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-bg-surface border border-border rounded-[6px] p-5">
              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div>
                  <label className="block text-[12px] uppercase font-medium text-text-secondary tracking-wide mb-2">
                    Target Domain
                  </label>
                  <input
                    type="text"
                    value={domain}
                    onChange={handleDomainChange}
                    placeholder="example.com"
                    className="w-full bg-bg-base border border-border focus:border-accent text-text-primary px-3 py-2 rounded-[4px] outline-none transition-colors text-[14px]"
                    spellCheck={false}
                    autoComplete="off"
                    disabled={loading}
                  />
                  {validationErr && (
                    <p className="text-red text-[12px] mt-2 font-medium">
                      {validationErr}
                    </p>
                  )}
                  {scanError && (
                    <p className="text-red text-[12px] mt-2 font-medium">
                      {scanError}
                    </p>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={loading || !domain.trim()}
                  className="btn-primary w-full"
                >
                  {loading ? 'Starting...' : 'Run Scan'}
                </button>
              </form>
            </div>
            
            <div className="bg-bg-surface border border-border rounded-[6px] p-5">
              <h2 className="text-[12px] uppercase font-medium text-text-secondary tracking-wide mb-3">
                System Status
              </h2>
              <div className="flex items-center gap-2 text-[13px] text-text-primary">
                <span className="w-2 h-2 rounded-full bg-green inline-block"></span>
                Services Operational
              </div>
            </div>
          </div>

          {/* Right Column: Scans Table */}
          <div className="lg:col-span-2">
            <h2 className="text-[14px] font-semibold text-text-primary mb-4">Recent Scans</h2>
            
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Target</th>
                    <th>Status</th>
                    <th>Subdomains</th>
                    <th>Started</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {scansLoading ? (
                    [1, 2, 3].map((i) => (
                      <tr key={i}>
                        <td colSpan={6} className="py-2">
                          <div className="h-4 bg-bg-elevated animate-pulse-subtle rounded w-full" />
                        </td>
                      </tr>
                    ))
                  ) : scans.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-text-muted">
                        <div className="text-2xl mb-2 opacity-50">◎</div>
                        <div className="text-[13px]">No recent scans found.</div>
                      </td>
                    </tr>
                  ) : (
                    scans.map((scan) => {
                      const id = String(getScanId(scan) || '')
                      return (
                        <tr key={id}>
                          <td className="font-mono text-text-muted text-[12px]">
                            {id ? id.substring(0, 8) : '—'}
                          </td>
                          <td className="font-medium text-text-primary">
                            {scan.domain || scan.target}
                          </td>
                          <td>
                            <StatusBadge status={scan.status} dot />
                          </td>
                          <td className="text-text-secondary">
                            {getSubdomainCount(scan)}
                          </td>
                          <td className="text-text-secondary text-[12px]">
                            {formatRelativeTime(scan.created_at ?? scan.createdAt)}
                          </td>
                          <td className="text-right">
                            <div className="flex items-center justify-end gap-3 text-[13px] font-medium">
                              <button
                                onClick={() => navigate(`/scan/${id}`)}
                                className="text-accent hover:text-accent-hover transition-colors"
                              >
                                View
                              </button>
                              <button
                                onClick={() => handleDelete(id)}
                                className="text-text-muted hover:text-red transition-colors"
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
            
          </div>
        </div>
      </main>
    </div>
  )
}
