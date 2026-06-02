import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { getScan, exportScan, regenerateSummary, downloadPdfReport } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import PipelineProgress from '../components/PipelineProgress'
import MetricCard from '../components/MetricCard'
import TabView from '../components/TabView'

// ── Constants ─────────────────────────────────────────────────────────────────

const DANGEROUS_PORTS = new Set([21, 22, 23, 25, 53, 110, 135, 139, 143, 445, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017])
const WEB_PORTS       = new Set([80, 443])

// ── Severity helpers ─────────────────────────────────────────────────────────

const VULN_SEVERITY_STYLE = {
  critical: { bg: 'bg-red/10', text: 'text-red',    badge: 'bg-red text-white' },
  high:     { bg: 'bg-orange/10', text: 'text-orange', badge: 'bg-orange text-white' },
  medium:   { bg: 'bg-blue/10', text: 'text-blue',   badge: 'bg-blue text-white' },
  low:      { bg: 'bg-bg-elevated', text: 'text-text-secondary', badge: 'bg-bg-elevated text-text-secondary border border-border' },
  info:     { bg: 'bg-bg-base', text: 'text-text-muted', badge: 'bg-bg-base text-text-muted border border-border' },
}

const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3, info: 4 }

function getVulnStyle(severity = 'info') {
  return VULN_SEVERITY_STYLE[severity.toLowerCase()] ?? VULN_SEVERITY_STYLE.info
}

function SeverityBadge({ severity = 'info', className = '' }) {
  const style = getVulnStyle(severity)
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${style.badge} ${className}`}>
      {severity}
    </span>
  )
}

// ── Secret classification ─────────────────────────────────────────────────────

const SECRET_STYLE_MAP = {
  aws_access_key:    { label: 'AWS Key',       color: 'bg-red text-white' },
  aws_secret_key:    { label: 'AWS Secret',    color: 'bg-red text-white' },
  private_key:       { label: 'Private Key',   color: 'bg-red text-white' },
  rsa_private_key:   { label: 'RSA Key',       color: 'bg-red text-white' },
  jwt_token:         { label: 'JWT',           color: 'bg-orange text-white' },
  api_key:           { label: 'API Key',       color: 'bg-orange text-white' },
  github_token:      { label: 'GitHub Token',  color: 'bg-blue text-white' },
  slack_token:       { label: 'Slack Token',   color: 'bg-blue text-white' },
  google_api_key:    { label: 'Google Key',    color: 'bg-blue text-white' },
}

function getSecretStyle(type = '') {
  const lower = type.toLowerCase().replace(/[^a-z_]/g, '_')
  const exact = SECRET_STYLE_MAP[lower]
  if (exact) return exact
  for (const [k, v] of Object.entries(SECRET_STYLE_MAP)) {
    if (lower.includes(k) || k.includes(lower)) return v
  }
  return { label: type, color: 'bg-bg-elevated text-text-secondary border border-border' }
}

function getSecretSeverityBadge(severity = 'medium') {
  return getVulnStyle(severity).badge
}

// ── Tech pill colors ──────────────────────────────────────────────────────────

function getTechColor(tech = '') {
  return 'bg-bg-elevated text-text-secondary border border-border'
}

// ── Provider badges ───────────────────────────────────────────────────────────

const PROVIDER_ICONS = {
  github: '🐙', heroku: '💜', aws: '☁️', azure: '🔷', gcp: '🌐',
  google: '🌐', shopify: '🛍️', fastly: '⚡', pantheon: '🐍',
  bitbucket: '🪣', gitlab: '🦊', sendgrid: '📧', zendesk: '💬',
  unbounce: '📢', surge: '🌊', default: '⚠️',
}

function getProviderIcon(cname = '') {
  const lower = cname.toLowerCase()
  for (const [k, v] of Object.entries(PROVIDER_ICONS)) {
    if (lower.includes(k)) return v
  }
  return PROVIDER_ICONS.default
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(dateStr) {
  if (!dateStr) return '—'
  try {
    const utcStr = dateStr.endsWith('Z') ? dateStr : `${dateStr}Z`
    return new Date(utcStr).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return '—' }
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return '—'
  const utcStr = dateStr.endsWith('Z') ? dateStr : `${dateStr}Z`
  const date = new Date(utcStr)
  if (isNaN(date)) return '—'
  const diffMs = Date.now() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  return formatDate(dateStr)
}

function statusCodeColor(code) {
  const n = parseInt(code, 10)
  if (!n) return 'text-text-muted'
  if (n >= 200 && n < 300) return 'text-green'
  if (n >= 300 && n < 400) return 'text-blue'
  if (n >= 400 && n < 500) return 'text-orange'
  if (n >= 500) return 'text-red'
  return 'text-text-secondary'
}

function portColor(port) {
  const n = parseInt(port, 10)
  if (WEB_PORTS.has(n)) return 'text-green'
  if (DANGEROUS_PORTS.has(n)) return 'text-red'
  return 'text-text-secondary'
}

function isHighlightEndpoint(url = '') {
  return /\/(api|v\d|admin|auth|login|graphql|swagger|debug|config|secret)\//i.test(url) ||
    /\/(api|v\d|admin|auth|login|graphql|swagger|debug|config|secret)$/i.test(url)
}

// ── Spinner ───────────────────────────────────────────────────────────────────

function Spinner({ size = 'md', color = 'var(--accent)' }) {
  const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-10 h-10' }
  return (
    <svg className={`${sizes[size]} animate-spin`} fill="none" viewBox="0 0 24 24" style={{ color }}>
      <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
    </svg>
  )
}

// ── OVERVIEW TAB ──────────────────────────────────────────────────────────────

function OverviewTab({ scan }) {
  const subdomains  = scan.subdomains ?? []
  
  // Use explicit counts from backend, fallback to array lengths for backwards compatibility
  const totalSubdomains  = scan.subdomains_count ?? subdomains.length
  const liveHostsCount   = scan.live_hosts_count ?? subdomains.filter((s) => s.is_alive || s.alive || s.live).length
  const totalPortsCount  = scan.ports_count ?? subdomains.reduce((acc, s) => acc + (s.ports?.length ?? 0), 0)
  const screenshotsCount = scan.screenshots_count ?? subdomains.filter(s => s.screenshot_path).length
  
  const secrets     = scan.secrets ?? []
  const endpoints   = scan.endpoints ?? []
  const takeovers   = scan.takeover_risks ?? scan.takeovers ?? []
  const vulns       = scan.vulnerability_findings ?? []
  
  return (
    <div className="animate-fade-in">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="Total Subdomains" value={totalSubdomains} />
        <MetricCard label="Live Hosts"        value={liveHostsCount} />
        <MetricCard label="Open Ports"        value={totalPortsCount} />
        <MetricCard
          label="Vulnerabilities"
          value={vulns.length}
          variant={vulns.length > 0 ? 'danger' : 'default'}
        />
        <MetricCard
          label="Secrets Detected"
          value={secrets.length}
          variant={secrets.length > 0 ? 'danger' : 'default'}
        />
        <MetricCard label="Endpoints Found"  value={endpoints.length} />
        <MetricCard
          label="Takeover Risks"
          value={takeovers.length}
          variant={takeovers.length > 0 ? 'danger' : 'default'}
        />
        <MetricCard label="Screenshots" value={screenshotsCount} />
      </div>
    </div>
  )
}

// ── SUBDOMAINS TAB ────────────────────────────────────────────────────────────

function SubdomainsTab({ subdomains = [], scanId }) {
  const [query, setQuery] = useState('')

  const sorted = [...subdomains].sort((a, b) => {
    const aAlive = a.is_alive || a.alive || a.live || false
    const bAlive = b.is_alive || b.alive || b.live || false
    return bAlive - aAlive
  })

  const filtered = sorted.filter((s) => {
    if (!query) return true
    const q = query.toLowerCase()
    return (s.subdomain ?? s.host ?? s.domain ?? '').toLowerCase().includes(q)
  })

  return (
    <div className="animate-fade-in space-y-4">
      <div className="relative max-w-sm">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter subdomains..."
          className="w-full bg-bg-surface border border-border focus:border-accent text-text-primary px-3 py-2 rounded-[4px] outline-none transition-colors text-[13px]"
        />
      </div>

      <div className="bg-bg-surface border border-border rounded-[6px] overflow-hidden">
        {filtered.length === 0 ? (
          <div className="py-12 text-center text-text-muted text-[13px]">
            {subdomains.length === 0 ? 'No subdomains discovered yet.' : 'No matching subdomains.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Subdomain</th>
                  <th>Status</th>
                  <th>Title</th>
                  <th>Technologies</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s, i) => {
                  const host   = s.subdomain ?? s.host ?? s.domain ?? `host-${i}`
                  const alive  = s.is_alive ?? s.alive ?? s.live ?? false
                  const code   = s.status_code ?? s.http_status ?? ''
                  const title  = s.title ?? s.page_title ?? ''
                  const techs  = s.technologies ?? s.tech ?? []

                  return (
                    <tr key={host + i}>
                      <td>
                        <a
                          href={`https://${host}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-[13px] text-text-primary hover:text-accent transition-colors"
                        >
                          {host}
                        </a>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <span className={`w-1.5 h-1.5 rounded-full ${alive ? 'bg-green' : 'bg-red'}`} />
                          {code && (
                            <span className={`font-mono text-[12px] font-medium ${statusCodeColor(code)}`}>
                              {code}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="text-text-secondary text-[13px] max-w-[200px] truncate" title={title}>
                        {title || '—'}
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {Array.isArray(techs) && techs.slice(0, 3).map((t, ti) => (
                            <span
                              key={ti}
                              className={`px-1.5 py-0.5 rounded text-[10px] font-medium bg-bg-elevated text-text-secondary border border-border`}
                            >
                              {t}
                            </span>
                          ))}
                          {techs.length > 3 && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-bg-base text-text-muted border border-border">
                              +{techs.length - 3}
                            </span>
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
    </div>
  )
}

// ── GALLERY TAB ───────────────────────────────────────────────────────────────

function GalleryTab({ subdomains = [], scanId }) {
  const [modal, setModal] = useState(null)
  const withScreenshots = subdomains.filter(s => s.screenshot_path && s.is_alive)

  if (withScreenshots.length === 0) {
    return (
      <div className="animate-fade-in py-16 text-center">
        <div className="text-2xl mb-2 opacity-30 text-text-muted">📷</div>
        <p className="text-text-muted text-[13px]">No screenshots captured yet.</p>
      </div>
    )
  }

  return (
    <div className="animate-fade-in space-y-4">
      {modal && (
        <div
          className="fixed inset-0 z-[100] bg-bg-base/90 flex items-center justify-center p-4"
          onClick={() => setModal(null)}
        >
          <div className="relative max-w-5xl w-full" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-2">
               <div className="font-mono text-text-primary text-[13px]">{modal.host}</div>
               <button
                 className="text-text-muted hover:text-text-primary text-[13px]"
                 onClick={() => setModal(null)}
               >
                 Close
               </button>
            </div>
            <img
              src={modal.url}
              alt={modal.host}
              className="w-full rounded-[6px] border border-border"
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-3">
        {withScreenshots.map((s, i) => {
          const host  = s.subdomain ?? `host-${i}`
          const code  = s.status_code
          const ssUrl = `/api/scan/${scanId}/screenshot/${s.id}`

          return (
            <div
              key={host}
              className="border border-border rounded-[6px] overflow-hidden cursor-pointer hover:border-border-active transition-colors bg-bg-surface flex flex-col"
              onClick={() => setModal({ url: ssUrl, host, code })}
            >
              <div className="h-[140px] bg-bg-base relative">
                <img
                  src={ssUrl}
                  alt={host}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.style.display = 'none'
                  }}
                />
              </div>
              <div className="p-3 bg-bg-surface border-t border-border flex justify-between items-center">
                <div className="font-mono text-text-primary text-[12px] truncate" title={host}>
                  {host}
                </div>
                {code && (
                  <div className={`font-mono text-[11px] font-medium ${statusCodeColor(code)}`}>
                    {code}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── PORTS TAB ─────────────────────────────────────────────────────────────────

function PortsTab({ ports = [] }) {
  if (ports.length === 0) {
    return (
      <div className="animate-fade-in py-16 text-center">
        <p className="text-text-muted text-[13px]">No open ports discovered.</p>
      </div>
    )
  }

  const grouped = ports.reduce((acc, p) => {
    const host = p.subdomain || 'unknown'
    if (!acc[host]) acc[host] = []
    acc[host].push(p)
    return acc
  }, {})

  return (
    <div className="animate-fade-in space-y-6">
      {Object.entries(grouped).map(([host, hostPorts], si) => (
        <div key={host + si} className="bg-bg-surface border border-border rounded-[6px] overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center gap-3 bg-bg-elevated">
            <span className="font-mono text-text-primary text-[13px] font-medium">{host}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Port</th>
                  <th>Protocol</th>
                  <th>Service</th>
                  <th>Version / Banner</th>
                </tr>
              </thead>
              <tbody>
                {hostPorts.map((p, pi) => {
                  const port     = p.port ?? p.number ?? p
                  const protocol = p.protocol ?? 'tcp'
                  const service  = p.service ?? p.name ?? '—'
                  const version  = p.version ?? p.banner ?? p.product ?? ''

                  return (
                    <tr key={pi}>
                      <td>
                        <span className={`font-mono font-medium text-[13px] ${portColor(port)}`}>
                          {port}
                        </span>
                      </td>
                      <td className="font-mono text-text-secondary text-[12px] uppercase">{protocol}</td>
                      <td className="text-text-primary text-[13px]">{service}</td>
                      <td className="font-mono text-text-muted text-[12px] max-w-[200px] truncate" title={version}>
                        {version || '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── SECRETS TAB ───────────────────────────────────────────────────────────────

function SecretsTab({ secrets = [] }) {
  if (secrets.length === 0) {
    return (
      <div className="animate-fade-in py-16 text-center">
        <p className="text-text-muted text-[13px]">No secrets detected.</p>
      </div>
    )
  }

  return (
    <div className="animate-fade-in space-y-4">
      <div className="bg-bg-surface border border-border rounded-[6px] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Type</th>
                <th>Value Preview</th>
                <th>Source File</th>
                <th>Line</th>
              </tr>
            </thead>
            <tbody>
              {secrets.map((s, i) => {
                const type    = s.secret_type ?? s.type ?? s.kind ?? 'unknown'
                const fileUrl = s.file_url ?? s.url ?? s.source ?? s.js_file ?? ''
                const value   = s.matched_value ?? s.value ?? s.secret ?? s.match ?? ''
                const lineNum = s.line_number ?? s.line ?? s.line_num ?? '—'
                const sev     = (s.severity || 'medium').toLowerCase()
                const isValidated = s.validated

                return (
                  <tr key={i}>
                    <td>
                      <SeverityBadge severity={sev} />
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${getSecretStyle(type).color}`}>
                          {type}
                        </span>
                        {isValidated ? (
                          <span className="px-1.5 py-0.5 rounded bg-green/10 text-green text-[9px] font-bold uppercase tracking-wide">
                            VALID
                          </span>
                        ) : (
                          <span className="px-1.5 py-0.5 rounded bg-gray-500/10 text-text-muted text-[9px] font-bold uppercase tracking-wide">
                            UNVERIFIED
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="font-mono text-text-primary text-[12px]">
                        {value ? `${String(value).slice(0, 30)}...` : '—'}
                      </span>
                    </td>
                    <td className="max-w-[220px]">
                      {fileUrl ? (
                        <a
                          href={fileUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-blue text-[12px] hover:underline truncate block"
                          title={fileUrl}
                        >
                          {fileUrl.replace(/^https?:\/\/[^/]+/, '')}
                        </a>
                      ) : (
                        <span className="text-text-muted text-[12px]">—</span>
                      )}
                    </td>
                    <td className="font-mono text-text-secondary text-[12px]">{lineNum}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── VALIDATED SECRETS TAB ──────────────────────────────────────────────────────

function ValidatedSecretsTab({ secrets = [] }) {
  const validatedSecrets = secrets.filter((s) => s.validated)

  if (validatedSecrets.length === 0) {
    return (
      <div className="animate-fade-in py-16 text-center">
        <p className="text-text-muted text-[13px]">No validated secrets found.</p>
      </div>
    )
  }

  return (
    <div className="animate-fade-in space-y-4">
      <div className="bg-bg-surface border border-border rounded-[6px] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Type</th>
                <th>Found On</th>
                <th>Proof</th>
              </tr>
            </thead>
            <tbody>
              {validatedSecrets.map((s, i) => {
                const type    = s.secret_type ?? s.type ?? s.kind ?? 'unknown'
                const fileUrl = s.file_url ?? s.url ?? s.source ?? s.js_file ?? ''
                const proof   = s.validation_proof ?? 'Valid'
                const sev     = (s.severity || 'medium').toLowerCase()

                return (
                  <tr key={i}>
                    <td>
                      <SeverityBadge severity={sev} />
                    </td>
                    <td>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${getSecretStyle(type).color}`}>
                        {type}
                      </span>
                    </td>
                    <td className="max-w-[220px]">
                      {fileUrl ? (
                        <a
                          href={fileUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-blue text-[12px] hover:underline truncate block"
                          title={fileUrl}
                        >
                          {fileUrl.replace(/^https?:\/\/[^/]+/, '')}
                        </a>
                      ) : (
                        <span className="text-text-muted text-[12px]">—</span>
                      )}
                    </td>
                    <td>
                      <span className="font-mono text-text-primary text-[12px]">
                        {proof}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── ENDPOINTS TAB ─────────────────────────────────────────────────────────────

const ENDPOINTS_PER_PAGE = 50

function EndpointsTab({ endpoints = [] }) {
  const [query, setQuery]   = useState('')
  const [page, setPage]     = useState(1)

  const filtered = endpoints.filter((ep) => {
    if (!query) return true
    const url = ep.url ?? ep.endpoint ?? ep.path ?? String(ep)
    return url.toLowerCase().includes(query.toLowerCase())
  })

  const totalPages = Math.ceil(filtered.length / ENDPOINTS_PER_PAGE)
  const paginated  = filtered.slice((page - 1) * ENDPOINTS_PER_PAGE, page * ENDPOINTS_PER_PAGE)

  useEffect(() => setPage(1), [query])

  return (
    <div className="animate-fade-in space-y-4">
      <div className="relative max-w-sm">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter endpoints..."
          className="w-full bg-bg-surface border border-border focus:border-accent text-text-primary px-3 py-2 rounded-[4px] outline-none transition-colors text-[13px]"
        />
      </div>

      <div className="bg-bg-surface border border-border rounded-[6px] overflow-hidden">
        {paginated.length === 0 ? (
          <div className="py-12 text-center text-text-muted text-[13px]">
            {endpoints.length === 0 ? 'No endpoints extracted yet.' : 'No matching endpoints.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>URL / Path</th>
                  <th>Source JS File</th>
                </tr>
              </thead>
              <tbody>
                {paginated.map((ep, i) => {
                  const url    = ep.url ?? ep.endpoint ?? ep.path ?? String(ep)
                  const source = ep.source_file ?? ep.source ?? ep.js_file ?? ep.file ?? ''
                  const isHL   = isHighlightEndpoint(url)

                  return (
                    <tr key={i}>
                      <td>
                        <span className={`font-mono text-[13px] ${isHL ? 'text-accent' : 'text-text-primary'}`}>
                          {url}
                        </span>
                      </td>
                      <td className="max-w-[240px]">
                        {source ? (
                          <a
                            href={source}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono text-text-secondary hover:text-text-primary text-[12px] truncate block"
                            title={source}
                          >
                            {source.replace(/^https?:\/\/[^/]+/, '')}
                          </a>
                        ) : (
                          <span className="text-text-muted text-[12px]">—</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-[13px]">
          <span className="text-text-secondary">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-ghost"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn-ghost"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── TAKEOVER RISKS TAB ────────────────────────────────────────────────────────

function TakeoverTab({ takeovers = [] }) {
  if (takeovers.length === 0) {
    return (
      <div className="animate-fade-in py-16 text-center">
        <p className="text-text-muted text-[13px]">No takeover risks detected.</p>
      </div>
    )
  }

  return (
    <div className="animate-fade-in space-y-4">
      <div className="bg-bg-surface border border-border rounded-[6px] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Subdomain</th>
                <th>CNAME Target</th>
                <th>Provider</th>
                <th>Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {takeovers.map((t, i) => {
                const subdomain = t.subdomain ?? t.host ?? t.domain ?? `host-${i}`
                const cname     = t.cname ?? t.cname_target ?? t.target ?? '—'
                const provider  = t.provider ?? cname

                return (
                  <tr key={i}>
                    <td>
                      <span className="font-mono text-[13px] text-text-primary">{subdomain}</span>
                    </td>
                    <td>
                      <span className="font-mono text-[12px] text-text-secondary">{cname}</span>
                    </td>
                    <td>
                      <span className="text-[13px] text-text-secondary capitalize">
                        {t.provider ?? (cname !== '—' ? cname.split('.')[0] : 'Unknown')}
                      </span>
                    </td>
                    <td>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-red text-white">
                        HIGH RISK
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── VULNERABILITIES TAB ───────────────────────────────────────────────────────

function VulnerabilitiesTab({ vulns = [] }) {
  if (vulns.length === 0) {
    return (
      <div className="animate-fade-in py-16 text-center">
        <p className="text-text-muted text-[13px]">No vulnerabilities detected.</p>
      </div>
    )
  }

  return (
    <div className="animate-fade-in space-y-4">
      <div className="bg-bg-surface border border-border rounded-[6px] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Template ID</th>
                <th>Name</th>
                <th>Host</th>
                <th>Matched At</th>
              </tr>
            </thead>
            <tbody>
              {vulns.map((v, i) => {
                const sev = (v.severity || 'info').toLowerCase()
                return (
                  <tr key={v.id || i}>
                    <td>
                      <SeverityBadge severity={sev} />
                    </td>
                    <td className="font-mono text-[12px] text-text-secondary">{v.template_id}</td>
                    <td className="text-[13px] font-medium text-text-primary">{v.template_name}</td>
                    <td className="font-mono text-[12px] text-text-primary">{v.host}</td>
                    <td className="font-mono text-[12px] text-text-secondary max-w-[200px] truncate" title={v.matched_at}>
                      {v.matched_at}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── AI SUMMARY TAB ────────────────────────────────────────────────────────────

function AISummaryTab({ scan, onRegenerate, isRegenerating }) {
  const aiSummaryObj = scan.ai_summary
  const summary   = aiSummaryObj?.summary_text ?? scan.summary_text ?? scan.summary
  const createdAt = aiSummaryObj?.created_at ?? scan.summary_created_at ?? scan.summary_at

  return (
    <div className="animate-fade-in space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-[14px] font-semibold text-text-primary">
          AI-Generated Summary
        </h3>
        <button
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="btn-outline text-[13px] py-1.5 px-3"
        >
          {isRegenerating ? 'Regenerating...' : 'Regenerate Summary'}
        </button>
      </div>

      {isRegenerating ? (
        <div className="py-12 flex flex-col items-center gap-4 text-center">
          <Spinner size="md" />
          <p className="text-text-muted text-[13px]">Regenerating AI summary...</p>
        </div>
      ) : !summary ? (
        <div className="py-12 flex flex-col items-center gap-4 text-center">
          <Spinner size="md" />
          <p className="text-text-muted text-[13px]">Generating AI summary...</p>
        </div>
      ) : (
        <div className="bg-bg-surface border border-border rounded-[6px] p-6">
          {createdAt && (
            <p className="text-text-secondary text-[12px] font-mono mb-6 pb-4 border-b border-border">
              Generated {formatRelativeTime(createdAt)}
            </p>
          )}
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {summary}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}

// ── MAIN SCAN DETAIL ──────────────────────────────────────────────────────────

export default function ScanDetail() {
  const { id }   = useParams()
  const [scan, setScan]                         = useState(null)
  const [loading, setLoading]                   = useState(true)
  const [error, setError]                       = useState(null)
  const [activeTab, setActiveTab]               = useState('overview')
  const [isRegeneratingAI, setIsRegeneratingAI] = useState(false)
  const [exportLoading, setExportLoading]       = useState(false)
  const [pdfLoading, setPdfLoading]             = useState(false)
  const [pollStatus, setPollStatus]             = useState('')
  const timeoutRef = useRef(null)
  const startTimeRef = useRef(Date.now())

  const fetchScan = useCallback(async () => {
    try {
      const data = await getScan(id)
      setScan(data)
      setError(null)
    } catch (ex) {
      if (ex.isTimeout) {
        // Do not set error for timeout, keep showing current UI and polling
        console.warn('Scan poll timed out, will retry...')
      } else {
        setError(ex?.response?.data?.error ?? ex?.message ?? 'Failed to load scan.')
      }
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchScan()
  }, [fetchScan])

  useEffect(() => {
    if (!scan) return
    const status = (scan.status ?? '').toLowerCase()
    const isActive = status === 'queued' || status === 'running'

    if (!isActive) {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      setPollStatus('')
      return
    }

    let isSubscribed = true

    const poll = async () => {
      if (!isSubscribed) return
      
      const elapsedMs = Date.now() - startTimeRef.current
      const elapsedSec = elapsedMs / 1000

      let intervalMs = 3000
      if (elapsedSec > 600) {
        setPollStatus('Scan may have failed - check console')
        return // stop polling after 10m
      } else if (elapsedSec > 150) {
        intervalMs = 10000
      } else if (elapsedSec > 30) {
        intervalMs = 5000
      }

      setPollStatus(`Checking every ${intervalMs / 1000}s...`)
      
      await fetchScan()
      
      if (isSubscribed) {
        timeoutRef.current = setTimeout(poll, intervalMs)
      }
    }

    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(poll, 3000)

    return () => {
      isSubscribed = false
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [scan?.status, fetchScan])

  async function handleExport() {
    setExportLoading(true)
    try {
      const blob = await exportScan(id)
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `argus-${scan?.domain ?? id}-${Date.now()}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
    } finally {
      setExportLoading(false)
    }
  }

  async function handlePdfDownload() {
    setPdfLoading(true)
    try {
      const blob = await downloadPdfReport(id, scan?.domain)
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      const date = new Date().toISOString().slice(0, 10)
      a.href     = url
      a.download = `argus-sentinel-${scan?.domain ?? id}-${date}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('PDF download failed:', err)
    } finally {
      setPdfLoading(false)
    }
  }

  async function handleRegenerateAI() {
    setIsRegeneratingAI(true)
    try {
      const updated = await regenerateSummary(id)
      if (updated) {
        setScan((prev) => ({ ...prev, ...updated }))
      } else {
        await fetchScan()
      }
    } catch {
    } finally {
      setIsRegeneratingAI(false)
    }
  }

  const subdomains  = scan?.subdomains ?? []
  const secrets     = scan?.secrets ?? []
  const endpoints   = scan?.endpoints ?? []
  const takeovers   = scan?.takeover_risks ?? scan?.takeovers ?? []
  const vulns       = scan?.vulnerability_findings ?? []
  
  const totalSubdomainsCount = scan?.subdomains_count ?? subdomains.length
  const totalPortsCount      = scan?.ports_count ?? subdomains.reduce((acc, s) => acc + (s.ports?.length ?? 0), 0)
  const galleryCount         = scan?.screenshots_count ?? subdomains.filter(s => s.screenshot_path).length
  const validatedSecretsCount= secrets.filter(s => s.validated).length

  const tabs = [
    { id: 'overview',   label: 'Overview' },
    { id: 'subdomains', label: 'Subdomains', count: totalSubdomainsCount },
    { id: 'gallery',    label: 'Gallery',    count: galleryCount },
    { id: 'ports',      label: 'Ports',      count: totalPortsCount },
    { id: 'secrets',    label: 'Secrets',    count: secrets.length },
    { id: 'validated_secrets', label: 'Validated Secrets', count: validatedSecretsCount, dangerCount: true },
    { id: 'endpoints',  label: 'Endpoints',  count: endpoints.length },
    { id: 'takeover',   label: 'Takeover',   count: takeovers.length },
    { id: 'vulns',      label: 'Vulns',      count: vulns.length },
    { id: 'ai',         label: 'AI Summary' },
  ]

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-base flex items-center justify-center">
        <Spinner size="md" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-bg-base flex items-center justify-center flex-col gap-4">
        <p className="text-red font-medium">{error}</p>
        <Link to="/" className="btn-outline">← Back to Home</Link>
      </div>
    )
  }

  if (!scan) return null

  const status    = scan.status ?? 'queued'
  const domain    = scan.domain ?? scan.target ?? id
  const createdAt = scan.created_at ?? scan.createdAt
  const doneAt    = scan.completed_at ?? scan.finished_at ?? scan.updated_at

  return (
    <div className="min-h-screen bg-bg-base pb-12">
      
      {/* ── Top Bar ──────────────────────────────────────────── */}
      <header className="bg-bg-surface border-b border-border sticky top-0 z-10">
        <div className="max-w-[1400px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            
            <div className="flex items-center gap-6">
              <Link to="/" className="text-text-secondary hover:text-text-primary transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </Link>
              
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h1 className="text-[24px] font-semibold text-text-primary leading-none">
                    {domain}
                  </h1>
                  <StatusBadge status={status} dot />
                </div>
                <div className="text-text-secondary text-[13px]">
                  {status === 'running' || status === 'queued'
                    ? `Started ${formatRelativeTime(createdAt)} ${pollStatus ? `· ${pollStatus}` : ''}`
                    : `Started ${formatRelativeTime(createdAt)} ${doneAt ? `· Completed ${formatRelativeTime(doneAt)}` : ''}`
                  }
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handlePdfDownload}
                disabled={pdfLoading || status !== 'complete'}
                className="btn-outline"
                title={status !== 'complete' ? 'Available when scan is complete' : 'Download PDF Report'}
              >
                {pdfLoading ? 'Generating...' : 'PDF Report'}
              </button>
              <button
                onClick={handleExport}
                disabled={exportLoading}
                className="btn-outline"
              >
                {exportLoading ? 'Exporting...' : 'Export JSON'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-6 mt-8">
        {/* ── Pipeline Progress ─────────────────────────────────── */}
        <div className="bg-bg-surface border border-border rounded-[6px] p-6 mb-6">
          <PipelineProgress currentStage={scan.current_stage ?? scan.stage} status={status} />
        </div>

        {/* ── Tab View ─────────────────────────────────────────── */}
        <div className="bg-bg-surface border border-border rounded-[6px] animate-fade-in overflow-hidden">
          <TabView tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab}>
            {activeTab === 'overview'   && <OverviewTab   scan={scan} />}
            {activeTab === 'subdomains' && <SubdomainsTab subdomains={subdomains} scanId={id} />}
            {activeTab === 'gallery'    && <GalleryTab    subdomains={subdomains} scanId={id} />}
            {activeTab === 'ports'      && <PortsTab      ports={scan.ports ?? []} />}
            {activeTab === 'secrets'    && <SecretsTab    secrets={secrets} />}
            {activeTab === 'validated_secrets' && <ValidatedSecretsTab secrets={secrets} />}
            {activeTab === 'endpoints'  && <EndpointsTab  endpoints={endpoints} />}
            {activeTab === 'takeover'   && <TakeoverTab   takeovers={takeovers} />}
            {activeTab === 'vulns'      && <VulnerabilitiesTab vulns={vulns} />}
            {activeTab === 'ai'         && (
              <AISummaryTab
                scan={scan}
                onRegenerate={handleRegenerateAI}
                isRegenerating={isRegeneratingAI}
              />
            )}
          </TabView>
        </div>
      </main>

    </div>
  )
}
