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
  critical: { bg: 'bg-[#200000]', text: 'text-red-400',    border: 'border-red-900',    badge: 'bg-red-950 text-red-400 border-red-900',       dot: 'bg-red-500'    },
  high:     { bg: 'bg-[#1a0800]', text: 'text-orange-400', border: 'border-orange-900', badge: 'bg-orange-950 text-orange-400 border-orange-900', dot: 'bg-orange-500' },
  medium:   { bg: 'bg-[#1a1400]', text: 'text-yellow-400', border: 'border-yellow-900', badge: 'bg-yellow-950 text-yellow-400 border-yellow-900', dot: 'bg-yellow-500' },
  low:      { bg: 'bg-[#001420]', text: 'text-blue-400',   border: 'border-blue-900',   badge: 'bg-blue-950 text-blue-400 border-blue-900',       dot: 'bg-blue-400'   },
  info:     { bg: 'bg-[#111111]', text: 'text-[#888888]',  border: 'border-[#333333]',  badge: 'bg-[#1a1a1a] text-[#888888] border-[#333333]',    dot: 'bg-[#666666]'  },
}

const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3, info: 4 }

function getVulnStyle(severity = 'info') {
  return VULN_SEVERITY_STYLE[severity.toLowerCase()] ?? VULN_SEVERITY_STYLE.info
}

function SeverityBadge({ severity = 'info', className = '' }) {
  const style = getVulnStyle(severity)
  return (
    <span className={`pill border text-[0.6rem] font-bold uppercase tracking-wide ${style.badge} ${className}`}>
      {severity}
    </span>
  )
}

// ── Secret classification ─────────────────────────────────────────────────────

const SECRET_STYLE_MAP = {
  aws_access_key:    { label: 'AWS Key',       color: 'bg-red-950 text-red-400 border-red-900' },
  aws_secret_key:    { label: 'AWS Secret',    color: 'bg-red-950 text-red-400 border-red-900' },
  private_key:       { label: 'Private Key',   color: 'bg-red-950 text-red-400 border-red-900' },
  rsa_private_key:   { label: 'RSA Key',       color: 'bg-red-950 text-red-400 border-red-900' },
  jwt_token:         { label: 'JWT',           color: 'bg-orange-950 text-orange-400 border-orange-900' },
  api_key:           { label: 'API Key',       color: 'bg-orange-950 text-orange-400 border-orange-900' },
  github_token:      { label: 'GitHub Token',  color: 'bg-yellow-950 text-yellow-400 border-yellow-900' },
  slack_token:       { label: 'Slack Token',   color: 'bg-yellow-950 text-yellow-400 border-yellow-900' },
  google_api_key:    { label: 'Google Key',    color: 'bg-yellow-950 text-yellow-400 border-yellow-900' },
}

function getSecretStyle(type = '') {
  const lower = type.toLowerCase().replace(/[^a-z_]/g, '_')
  const exact = SECRET_STYLE_MAP[lower]
  if (exact) return exact
  for (const [k, v] of Object.entries(SECRET_STYLE_MAP)) {
    if (lower.includes(k) || k.includes(lower)) return v
  }
  return { label: type, color: 'bg-[#1a1a1a] text-[#888888] border-[#333333]' }
}

function getSecretSeverityBadge(severity = 'medium') {
  return getVulnStyle(severity).badge
}

// ── Tech pill colors ──────────────────────────────────────────────────────────

const TECH_COLORS = {
  react:        'bg-[#001a2e] text-[#61dafb] border-[#0a3a5a]',
  angular:      'bg-[#1a0000] text-[#dd1b16] border-[#3a0000]',
  vue:          'bg-[#001a10] text-[#42b883] border-[#004422]',
  next:         'bg-[#0a0a0a] text-white border-[#444444]',
  nginx:        'bg-[#001a00] text-[#009639] border-[#003a00]',
  apache:       'bg-[#1a0a00] text-[#d22128] border-[#3a1500]',
  cloudflare:   'bg-[#001018] text-[#f48120] border-[#1a2a10]',
  wordpress:    'bg-[#001428] text-[#21759b] border-[#002a45]',
  jquery:       'bg-[#001020] text-[#0769ad] border-[#002040]',
  bootstrap:    'bg-[#1a0030] text-[#7952b3] border-[#2a0050]',
  php:          'bg-[#0a0a1e] text-[#8892be] border-[#1a1a3e]',
  django:       'bg-[#001209] text-[#0c4b33] border-[#002a18]',
  express:      'bg-[#0a0a0a] text-[#aaaaaa] border-[#333333]',
  laravel:      'bg-[#1e0600] text-[#ff2d20] border-[#3a0a00]',
  default:      'bg-[#1a1a1a] text-[#888888] border-[#2a2a2a]',
}

function getTechColor(tech = '') {
  const lower = tech.toLowerCase()
  for (const [k, v] of Object.entries(TECH_COLORS)) {
    if (lower.includes(k)) return v
  }
  return TECH_COLORS.default
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
    return new Date(dateStr).toLocaleString(undefined, {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return '—' }
}

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
  return formatDate(dateStr)
}

function statusCodeColor(code) {
  const n = parseInt(code, 10)
  if (!n) return 'text-[#555555]'
  if (n >= 200 && n < 300) return 'text-[#00ff88]'
  if (n >= 300 && n < 400) return 'text-[#ffcc00]'
  if (n >= 400 && n < 500) return 'text-[#ff8844]'
  if (n >= 500) return 'text-[#ff4444]'
  return 'text-[#888888]'
}

function portColor(port) {
  const n = parseInt(port, 10)
  if (WEB_PORTS.has(n)) return 'text-[#00ff88]'
  if (DANGEROUS_PORTS.has(n)) return 'text-[#ff4444]'
  return 'text-[#aaaaaa]'
}

function isHighlightEndpoint(url = '') {
  return /\/(api|v\d|admin|auth|login|graphql|swagger|debug|config|secret)\//i.test(url) ||
    /\/(api|v\d|admin|auth|login|graphql|swagger|debug|config|secret)$/i.test(url)
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

// ── Spinner ───────────────────────────────────────────────────────────────────

function Spinner({ size = 'md', color = '#00ff88' }) {
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
  const liveHosts   = subdomains.filter((s) => s.is_alive || s.alive || s.live)
  const totalPorts  = subdomains.reduce((acc, s) => acc + (s.ports?.length ?? 0), 0)
  const secrets     = scan.secrets ?? []
  const endpoints   = scan.endpoints ?? []
  const takeovers   = scan.takeover_risks ?? scan.takeovers ?? []
  const vulns       = scan.vulnerability_findings ?? []
  const critHighVulns = vulns.filter(v => ['critical','high'].includes((v.severity || '').toLowerCase()))
  const critHighSecrets = secrets.filter(s => ['critical','high'].includes((s.severity || '').toLowerCase()))

  return (
    <div className="animate-slide-up">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard icon="🌐" label="Total Subdomains" value={subdomains.length} />
        <MetricCard icon="💓" label="Live Hosts"        value={liveHosts.length} />
        <MetricCard icon="🔌" label="Open Ports"        value={totalPorts} />
        <MetricCard
          icon="🎯"
          label="Vulnerabilities"
          value={vulns.length}
          variant={critHighVulns.length > 0 ? 'danger' : vulns.length > 0 ? 'warning' : 'default'}
          subtitle={critHighVulns.length > 0 ? `${critHighVulns.length} critical/high` : undefined}
        />
        <MetricCard
          icon="🔑"
          label="Secrets Detected"
          value={secrets.length}
          variant={critHighSecrets.length > 0 ? 'danger' : secrets.length > 0 ? 'warning' : 'default'}
          subtitle={critHighSecrets.length > 0 ? 'Immediate attention required' : undefined}
        />
        <MetricCard icon="🗺️" label="Endpoints Found"  value={endpoints.length} />
        <MetricCard
          icon="⚠️"
          label="Takeover Risks"
          value={takeovers.length}
          variant={takeovers.length > 0 ? 'danger' : 'default'}
          subtitle={takeovers.length > 0 ? 'Subdomain takeover detected' : undefined}
        />
        <MetricCard icon="📸" label="Screenshots" value={subdomains.filter(s => s.screenshot_path).length} />
      </div>

      {/* Scan metadata */}
      <div className="mt-8 card p-5 text-sm">
        <h3 className="text-[0.65rem] font-bold tracking-[0.15em] uppercase text-[#555555] mb-4">
          Scan Metadata
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Scan ID',   value: scan.id ?? scan._id ?? scan.scan_id ?? '—' },
            { label: 'Target',    value: scan.domain ?? scan.target ?? '—' },
            { label: 'Status',    value: scan.status ?? '—' },
            { label: 'Stage',     value: scan.current_stage ?? scan.stage ?? 'N/A' },
          ].map(({ label, value }) => (
            <div key={label}>
              <div className="text-[#555555] text-[0.65rem] uppercase tracking-widest mb-1">{label}</div>
              <div className="font-mono text-[#aaaaaa] text-sm truncate">{String(value)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── SUBDOMAINS TAB ────────────────────────────────────────────────────────────

function SubdomainsTab({ subdomains = [], scanId }) {
  const [query, setQuery] = useState('')
  const [screenshotModal, setScreenshotModal] = useState(null) // { url, host }

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
    <div className="animate-slide-up space-y-4">
      {/* Screenshot modal */}
      {screenshotModal && (
        <div
          className="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-4"
          onClick={() => setScreenshotModal(null)}
        >
          <div
            className="relative max-w-5xl w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="absolute -top-10 right-0 text-[#888888] hover:text-white text-sm"
              onClick={() => setScreenshotModal(null)}
            >
              ✕ Close
            </button>
            <div className="text-center mb-2 font-mono text-[#00ff88] text-sm">{screenshotModal.host}</div>
            <img
              src={screenshotModal.url}
              alt={screenshotModal.host}
              className="w-full rounded border border-[#333333]"
            />
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative max-w-sm">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#555555] text-sm">🔍</span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter subdomains..."
          className="input-dark pl-9 py-2 text-sm h-10"
        />
      </div>

      <div className="text-xs text-[#555555] font-mono">
        {filtered.length} / {subdomains.length} subdomains
      </div>

      <div className="card overflow-hidden">
        {filtered.length === 0 ? (
          <div className="py-12 text-center text-[#555555] text-sm">
            {subdomains.length === 0 ? 'No subdomains discovered yet.' : 'No matching subdomains.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Screenshot</th>
                  <th>Subdomain</th>
                  <th>Alive</th>
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
                  const ssUrl  = s.screenshot_path && scanId
                    ? `/api/scan/${scanId}/screenshot/${s.id}`
                    : null

                  return (
                    <tr key={host + i}>
                      <td>
                        {ssUrl ? (
                          <div
                            className="w-16 h-10 rounded overflow-hidden border border-[#333333] cursor-pointer hover:border-[#00ff88] transition-colors"
                            onClick={() => setScreenshotModal({ url: ssUrl, host })}
                          >
                            <img
                              src={ssUrl}
                              alt={host}
                              className="w-full h-full object-cover"
                              onError={(e) => { e.target.style.display = 'none'; e.target.parentElement.style.background = '#1a1a1a' }}
                            />
                          </div>
                        ) : (
                          <div className="w-16 h-10 rounded border border-[#222222] bg-[#0f0f0f] flex items-center justify-center text-[#333333] text-xs">
                            —
                          </div>
                        )}
                      </td>
                      <td>
                        <a
                          href={`https://${host}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-sm text-[#cccccc] hover:text-[#00ff88] transition-colors"
                        >
                          {host}
                        </a>
                      </td>
                      <td>
                        {alive ? (
                          <span className="inline-flex items-center gap-1.5 text-[#00ff88] text-xs font-semibold">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#00ff88] inline-block" />
                            ALIVE
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 text-[#ff4444] text-xs font-semibold">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#ff4444] inline-block opacity-60" />
                            DEAD
                          </span>
                        )}
                      </td>
                      <td>
                        <span className={`font-mono text-sm font-semibold ${statusCodeColor(code)}`}>
                          {code || '—'}
                        </span>
                      </td>
                      <td className="text-[#888888] text-sm max-w-[200px] truncate" title={title}>
                        {title || '—'}
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {Array.isArray(techs) && techs.slice(0, 4).map((t, ti) => (
                            <span
                              key={ti}
                              className={`pill border text-[0.6rem] ${getTechColor(t)}`}
                            >
                              {t}
                            </span>
                          ))}
                          {techs.length > 4 && (
                            <span className="pill bg-[#1a1a1a] text-[#555555] border border-[#2a2a2a]">
                              +{techs.length - 4}
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
      <div className="animate-slide-up card py-16 text-center">
        <div className="text-4xl mb-3 opacity-30">📸</div>
        <p className="text-[#555555] text-sm">No screenshots captured yet.</p>
        <p className="text-[#444444] text-xs mt-1">Screenshots are taken of live hosts during the scan.</p>
      </div>
    )
  }

  return (
    <div className="animate-slide-up space-y-4">
      {/* Modal */}
      {modal && (
        <div
          className="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-4"
          onClick={() => setModal(null)}
        >
          <div className="relative max-w-5xl w-full" onClick={(e) => e.stopPropagation()}>
            <button
              className="absolute -top-10 right-0 text-[#888888] hover:text-white text-sm"
              onClick={() => setModal(null)}
            >
              ✕ Close
            </button>
            <div className="text-center mb-2 font-mono text-[#00ff88] text-sm">{modal.host}</div>
            {modal.code && (
              <div className="text-center mb-3">
                <span className={`font-mono text-xs ${statusCodeColor(modal.code)}`}>{modal.code}</span>
              </div>
            )}
            <img
              src={modal.url}
              alt={modal.host}
              className="w-full rounded border border-[#333333]"
            />
          </div>
        </div>
      )}

      <div className="text-xs text-[#555555] font-mono">{withScreenshots.length} screenshot{withScreenshots.length !== 1 ? 's' : ''}</div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {withScreenshots.map((s, i) => {
          const host  = s.subdomain ?? `host-${i}`
          const techs = s.technologies ?? []
          const code  = s.status_code
          const ssUrl = `/api/scan/${scanId}/screenshot/${s.id}`

          return (
            <div
              key={host}
              className="card overflow-hidden cursor-pointer hover:border-[#00ff88]/30 transition-colors group"
              onClick={() => setModal({ url: ssUrl, host, code })}
            >
              {/* Screenshot thumbnail */}
              <div className="relative h-40 bg-[#0f0f0f] overflow-hidden">
                <img
                  src={ssUrl}
                  alt={host}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  onError={(e) => {
                    e.target.style.display = 'none'
                    e.target.parentElement.innerHTML = '<div class="flex items-center justify-center h-full text-[#333333] text-4xl">📷</div>'
                  }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>

              {/* Card info */}
              <div className="p-3 space-y-2">
                <div className="font-mono text-[#cccccc] text-xs truncate" title={host}>
                  {host}
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  {code && (
                    <span className={`font-mono text-xs font-bold ${statusCodeColor(code)}`}>{code}</span>
                  )}
                  {techs.slice(0, 3).map((t, ti) => (
                    <span key={ti} className={`pill border text-[0.55rem] ${getTechColor(t)}`}>
                      {t}
                    </span>
                  ))}
                  {techs.length > 3 && (
                    <span className="text-[0.55rem] text-[#555555]">+{techs.length - 3}</span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── PORTS TAB ─────────────────────────────────────────────────────────────────

function PortsTab({ subdomains = [] }) {
  const hostsWithPorts = subdomains.filter((s) => s.ports && s.ports.length > 0)

  if (hostsWithPorts.length === 0) {
    return (
      <div className="animate-slide-up card py-16 text-center">
        <div className="text-4xl mb-3 opacity-30">🔌</div>
        <p className="text-[#555555] text-sm">No open ports discovered.</p>
      </div>
    )
  }

  return (
    <div className="animate-slide-up space-y-6">
      {hostsWithPorts.map((s, si) => {
        const host = s.subdomain ?? s.host ?? s.domain ?? `host-${si}`
        return (
          <div key={host + si} className="card overflow-hidden">
            <div className="px-5 py-3 border-b border-[#1e1e1e] flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-[#00ff88] flex-shrink-0" />
              <span className="font-mono text-[#00ff88] text-sm font-semibold">{host}</span>
              <span className="text-[#444444] text-xs ml-auto">{s.ports.length} port{s.ports.length !== 1 ? 's' : ''}</span>
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
                  {s.ports.map((p, pi) => {
                    const port     = p.port ?? p.number ?? p
                    const protocol = p.protocol ?? 'tcp'
                    const service  = p.service ?? p.name ?? '—'
                    const version  = p.version ?? p.banner ?? p.product ?? ''
                    const isDangerous = DANGEROUS_PORTS.has(parseInt(port, 10))
                    const isWeb      = WEB_PORTS.has(parseInt(port, 10))

                    return (
                      <tr key={pi} className={isDangerous ? 'bg-[rgba(255,68,68,0.03)]' : ''}>
                        <td>
                          <span className={`font-mono font-bold text-sm ${portColor(port)}`}>
                            {port}
                          </span>
                          {isDangerous && (
                            <span className="ml-2 text-[0.55rem] text-[#ff4444] bg-[rgba(255,68,68,0.1)] border border-[rgba(255,68,68,0.3)] px-1.5 py-0.5 rounded uppercase tracking-wide">
                              sensitive
                            </span>
                          )}
                          {isWeb && (
                            <span className="ml-2 text-[0.55rem] text-[#00ff88] bg-[rgba(0,255,136,0.08)] border border-[rgba(0,255,136,0.2)] px-1.5 py-0.5 rounded uppercase tracking-wide">
                              web
                            </span>
                          )}
                        </td>
                        <td className="font-mono text-[#888888] text-sm uppercase">{protocol}</td>
                        <td className="text-[#cccccc] text-sm">{service}</td>
                        <td className="font-mono text-[#666666] text-xs max-w-[200px] truncate" title={version}>
                          {version || '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── SECRETS TAB ───────────────────────────────────────────────────────────────

const SECRET_SEVERITY_FILTERS = ['All', 'Critical', 'High', 'Medium', 'Low', 'Info']

function SecretsTab({ secrets = [] }) {
  const [filter, setFilter] = useState('All')

  const sorted = [...secrets].sort((a, b) => {
    const aOrder = SEVERITY_ORDER[(a.severity || 'medium').toLowerCase()] ?? 2
    const bOrder = SEVERITY_ORDER[(b.severity || 'medium').toLowerCase()] ?? 2
    return aOrder - bOrder
  })

  const filtered = sorted.filter(s => {
    if (filter === 'All') return true
    return (s.severity || 'medium').toLowerCase() === filter.toLowerCase()
  })

  const critCount   = secrets.filter(s => (s.severity || '').toLowerCase() === 'critical').length
  const highCount   = secrets.filter(s => (s.severity || '').toLowerCase() === 'high').length

  if (secrets.length === 0) {
    return (
      <div className="animate-slide-up card py-16 text-center">
        <div className="text-4xl mb-3">✅</div>
        <p className="text-[#00ff88] font-semibold">No secrets detected.</p>
        <p className="text-[#555555] text-xs mt-1">No API keys, tokens, or credentials found in JS files.</p>
      </div>
    )
  }

  return (
    <div className="animate-slide-up space-y-4">
      {/* Warning banner */}
      <div className="rounded-lg border border-[rgba(255,68,68,0.35)] bg-[#150a0a] p-4 flex items-start gap-3">
        <span className="text-[#ff4444] text-xl flex-shrink-0 mt-0.5">🚨</span>
        <div>
          <p className="text-[#ff4444] font-semibold text-sm">
            {secrets.length} secret{secrets.length !== 1 ? 's' : ''} detected
            {(critCount > 0 || highCount > 0) && (
              <span className="ml-2 text-xs">
                — {critCount > 0 && `${critCount} critical`}{critCount > 0 && highCount > 0 && ', '}{highCount > 0 && `${highCount} high`}
              </span>
            )}
          </p>
          <p className="text-[#884444] text-xs mt-0.5">
            Exposed credentials found in JavaScript files. Rotate these immediately.
          </p>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex gap-2 flex-wrap">
        {SECRET_SEVERITY_FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-all border ${
              filter === f
                ? 'bg-[#00ff88] text-black border-[#00ff88]'
                : 'bg-[#0f0f0f] text-[#666666] border-[#222222] hover:border-[#444444] hover:text-[#aaaaaa]'
            }`}
          >
            {f}
          </button>
        ))}
        <span className="ml-auto text-xs text-[#555555] font-mono self-center">
          {filtered.length} / {secrets.length}
        </span>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Confidence</th>
                <th>Type</th>
                <th>Source File</th>
                <th>Value Preview</th>
                <th>Line #</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => {
                const type    = s.secret_type ?? s.type ?? s.kind ?? 'unknown'
                const fileUrl = s.file_url ?? s.url ?? s.source ?? s.js_file ?? ''
                const value   = s.matched_value ?? s.value ?? s.secret ?? s.match ?? ''
                const lineNum = s.line_number ?? s.line ?? s.line_num ?? '—'
                const sev     = (s.severity || 'medium').toLowerCase()
                const conf    = s.confidence ?? 60
                const confColor = conf >= 80 ? '#00ff88' : conf >= 50 ? '#ffcc00' : '#ff6666'

                return (
                  <tr key={i}>
                    <td>
                      <SeverityBadge severity={sev} />
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${conf}%`, background: confColor }}
                          />
                        </div>
                        <span className="font-mono text-xs" style={{ color: confColor }}>{conf}%</span>
                      </div>
                    </td>
                    <td>
                      <span className={`pill border text-[0.6rem] ${getSecretStyle(type).color}`}>
                        {type}
                      </span>
                    </td>
                    <td className="max-w-[220px]">
                      {fileUrl ? (
                        <a
                          href={fileUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-[#00ff88] text-xs hover:underline truncate block"
                          title={fileUrl}
                        >
                          {fileUrl.replace(/^https?:\/\/[^/]+/, '')}
                        </a>
                      ) : (
                        <span className="text-[#555555] text-xs">—</span>
                      )}
                    </td>
                    <td>
                      <span className="font-mono text-[#aaaaaa] text-xs bg-[#1a1a1a] px-2 py-1 rounded">
                        {value ? `${String(value).slice(0, 20)}****` : '—'}
                      </span>
                    </td>
                    <td className="font-mono text-[#888888] text-sm">{lineNum}</td>
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
    <div className="animate-slide-up space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative max-w-sm flex-1">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#555555] text-sm">🔍</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter endpoints..."
            className="input-dark pl-9 py-2 text-sm h-10"
          />
        </div>
        <span className="text-xs text-[#555555] font-mono whitespace-nowrap">
          {filtered.length} endpoint{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="card overflow-hidden">
        {paginated.length === 0 ? (
          <div className="py-12 text-center text-[#555555] text-sm">
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
                    <tr key={i} className={isHL ? 'bg-[rgba(0,255,136,0.03)]' : ''}>
                      <td>
                        <div className="flex items-center gap-2">
                          {isHL && (
                            <span className="text-[#00ff88] text-xs opacity-70 flex-shrink-0">★</span>
                          )}
                          <span className={`font-mono text-sm ${isHL ? 'text-[#00ff88]' : 'text-[#cccccc]'}`}>
                            {url}
                          </span>
                        </div>
                      </td>
                      <td className="max-w-[240px]">
                        {source ? (
                          <a
                            href={source}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono text-[#555555] hover:text-[#888888] text-xs truncate block"
                            title={source}
                          >
                            {source.replace(/^https?:\/\/[^/]+/, '')}
                          </a>
                        ) : (
                          <span className="text-[#333333] text-xs">—</span>
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
        <div className="flex items-center justify-between text-sm">
          <span className="text-[#555555] text-xs font-mono">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-ghost py-1.5 px-3 text-xs disabled:opacity-30 disabled:cursor-not-allowed"
            >
              ← Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn-ghost py-1.5 px-3 text-xs disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Next →
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
      <div className="animate-slide-up card py-16 text-center">
        <div className="text-4xl mb-3">🛡️</div>
        <p className="text-[#00ff88] font-semibold text-base">No takeover risks detected.</p>
        <p className="text-[#555555] text-xs mt-1">All subdomains appear to be properly configured.</p>
      </div>
    )
  }

  return (
    <div className="animate-slide-up space-y-4">
      <div className="rounded-lg border border-[rgba(255,68,68,0.4)] bg-[#150a0a] p-4 flex items-start gap-3">
        <span className="text-2xl flex-shrink-0">⚠️</span>
        <div>
          <p className="text-[#ff4444] font-bold text-sm">
            {takeovers.length} subdomain takeover risk{takeovers.length !== 1 ? 's' : ''} detected
          </p>
          <p className="text-[#884444] text-xs mt-1">
            These subdomains point to unclaimed external services and may be vulnerable to takeover.
          </p>
        </div>
      </div>

      <div className="card overflow-hidden">
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
                const icon      = getProviderIcon(provider)

                return (
                  <tr key={i} className="bg-[rgba(255,68,68,0.025)]">
                    <td>
                      <span className="font-mono text-sm text-[#ff8844]">{subdomain}</span>
                    </td>
                    <td>
                      <span className="font-mono text-xs text-[#888888]">{cname}</span>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <span>{icon}</span>
                        <span className="text-sm text-[#cccccc] capitalize">
                          {t.provider ?? (cname !== '—' ? cname.split('.')[0] : 'Unknown')}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="pill border bg-red-950 text-red-400 border-red-900 text-[0.6rem]">
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

const VULN_FILTERS = ['All', 'Critical', 'High', 'Medium', 'Low', 'Info']

function VulnerabilitiesTab({ vulns = [] }) {
  const [filter, setFilter] = useState('All')
  const [expandedId, setExpandedId] = useState(null)

  const sorted = [...vulns].sort((a, b) => {
    const aO = SEVERITY_ORDER[(a.severity || 'info').toLowerCase()] ?? 4
    const bO = SEVERITY_ORDER[(b.severity || 'info').toLowerCase()] ?? 4
    return aO - bO
  })

  const filtered = sorted.filter(v => {
    if (filter === 'All') return true
    return (v.severity || 'info').toLowerCase() === filter.toLowerCase()
  })

  if (vulns.length === 0) {
    return (
      <div className="animate-slide-up card py-16 text-center">
        <div className="text-4xl mb-3">🛡️</div>
        <p className="text-[#00ff88] font-semibold">No vulnerabilities detected.</p>
        <p className="text-[#555555] text-xs mt-1">Nuclei scanner found no critical/high/medium issues.</p>
      </div>
    )
  }

  const counts = {
    critical: vulns.filter(v => v.severity === 'critical').length,
    high:     vulns.filter(v => v.severity === 'high').length,
    medium:   vulns.filter(v => v.severity === 'medium').length,
    low:      vulns.filter(v => v.severity === 'low').length,
    info:     vulns.filter(v => v.severity === 'info').length,
  }

  return (
    <div className="animate-slide-up space-y-4">
      {/* Alert banner */}
      <div className="rounded-lg border border-[rgba(255,68,68,0.35)] bg-[#150a0a] p-4 flex items-start gap-3">
        <span className="text-xl flex-shrink-0">🎯</span>
        <div>
          <p className="text-[#ff4444] font-semibold text-sm">
            {vulns.length} vulnerability finding{vulns.length !== 1 ? 's' : ''} —{' '}
            {counts.critical > 0 && <span className="text-red-400">{counts.critical} critical </span>}
            {counts.high > 0 && <span className="text-orange-400">{counts.high} high </span>}
            {counts.medium > 0 && <span className="text-yellow-400">{counts.medium} medium</span>}
          </p>
          <p className="text-[#884444] text-xs mt-0.5">
            Discovered by Nuclei template-based vulnerability scanner.
          </p>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex gap-2 flex-wrap">
        {VULN_FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-all border ${
              filter === f
                ? 'bg-[#00ff88] text-black border-[#00ff88]'
                : 'bg-[#0f0f0f] text-[#666666] border-[#222222] hover:border-[#444444] hover:text-[#aaaaaa]'
            }`}
          >
            {f}
            {f !== 'All' && counts[f.toLowerCase()] > 0 && (
              <span className="ml-1.5 text-[0.6rem] opacity-70">({counts[f.toLowerCase()]})</span>
            )}
          </button>
        ))}
        <span className="ml-auto text-xs text-[#555555] font-mono self-center">
          {filtered.length} / {vulns.length}
        </span>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Template ID</th>
                <th>Name</th>
                <th>Host</th>
                <th>Matched At</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((v, i) => {
                const sev    = (v.severity || 'info').toLowerCase()
                const style  = getVulnStyle(sev)
                const isExp  = expandedId === (v.id || i)
                const tags   = v.tags ?? []

                return (
                  <>
                    <tr
                      key={v.id || i}
                      className={`cursor-pointer ${style.bg} hover:brightness-125 transition-all`}
                      onClick={() => setExpandedId(isExp ? null : (v.id || i))}
                    >
                      <td>
                        <SeverityBadge severity={sev} />
                      </td>
                      <td className="font-mono text-xs text-[#888888]">{v.template_id}</td>
                      <td className="text-sm font-medium text-[#cccccc]">{v.template_name}</td>
                      <td className="font-mono text-xs text-[#00ff88]">{v.host}</td>
                      <td className="font-mono text-xs text-[#888888] max-w-[200px] truncate" title={v.matched_at}>
                        {v.matched_at}
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {tags.slice(0, 3).map((t, ti) => (
                            <span key={ti} className="pill bg-[#1a1a1a] text-[#555555] border border-[#2a2a2a] text-[0.55rem]">
                              {t}
                            </span>
                          ))}
                          {tags.length > 3 && <span className="text-[0.55rem] text-[#444444]">+{tags.length - 3}</span>}
                        </div>
                      </td>
                    </tr>
                    {isExp && (v.description || v.remediation) && (
                      <tr key={`${v.id || i}-expanded`} className={style.bg}>
                        <td colSpan={6} className="px-4 pb-4 pt-0">
                          {v.description && (
                            <div className="mb-2">
                              <span className="text-[0.65rem] font-bold uppercase tracking-widest text-[#555555]">Description</span>
                              <p className="text-xs text-[#aaaaaa] mt-1 leading-relaxed">{v.description}</p>
                            </div>
                          )}
                          {v.remediation && (
                            <div>
                              <span className="text-[0.65rem] font-bold uppercase tracking-widest text-[#00aa66]">Remediation</span>
                              <p className="text-xs text-[#aaaaaa] mt-1 leading-relaxed">{v.remediation}</p>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </>
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
    <div className="animate-slide-up space-y-5">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-xl">🤖</span>
          <h3 className="text-sm font-semibold text-[#888888] uppercase tracking-widest">
            AI-Generated Summary
          </h3>
        </div>
        <button
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="btn-ghost text-xs py-2 px-4 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isRegenerating ? (
            <span className="flex items-center gap-2">
              <Spinner size="sm" />
              Regenerating...
            </span>
          ) : (
            '⟳ Regenerate Summary'
          )}
        </button>
      </div>

      {isRegenerating ? (
        <div className="card p-12 flex flex-col items-center gap-4 text-center">
          <Spinner size="lg" />
          <p className="text-[#888888] text-sm">Regenerating AI summary...</p>
          <p className="text-[#555555] text-xs">This may take a moment.</p>
        </div>
      ) : !summary ? (
        <div className="card p-12 flex flex-col items-center gap-4 text-center">
          <div className="relative">
            <Spinner size="lg" />
          </div>
          <p className="text-[#888888] text-sm">Generating AI summary...</p>
          <p className="text-[#555555] text-xs">
            The AI is analyzing your scan results. This may take up to a minute.
          </p>
        </div>
      ) : (
        <div className="card p-6">
          {createdAt && (
            <p className="text-[#444444] text-xs font-mono mb-5">
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
  const intervalRef = useRef(null)

  // ── Fetch ────────────────────────────────────────────────────────────────

  const fetchScan = useCallback(async () => {
    try {
      const data = await getScan(id)
      setScan(data)
      setError(null)
    } catch (ex) {
      setError(ex?.response?.data?.error ?? ex?.message ?? 'Failed to load scan.')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchScan()
  }, [fetchScan])

  // ── Polling ──────────────────────────────────────────────────────────────

  useEffect(() => {
    if (!scan) return
    const status = (scan.status ?? '').toLowerCase()
    const isActive = status === 'queued' || status === 'running'

    if (isActive) {
      if (intervalRef.current) clearInterval(intervalRef.current)
      intervalRef.current = setInterval(fetchScan, 3000)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [scan?.status, fetchScan])

  // ── Export JSON ───────────────────────────────────────────────────────────

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
      // silently fail
    } finally {
      setExportLoading(false)
    }
  }

  // ── Download PDF ──────────────────────────────────────────────────────────

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

  // ── Regenerate AI ─────────────────────────────────────────────────────────

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
      // silently fail
    } finally {
      setIsRegeneratingAI(false)
    }
  }

  // ── Derived data ─────────────────────────────────────────────────────────

  const subdomains  = scan?.subdomains ?? []
  const secrets     = scan?.secrets ?? []
  const endpoints   = scan?.endpoints ?? []
  const takeovers   = scan?.takeover_risks ?? scan?.takeovers ?? []
  const vulns       = scan?.vulnerability_findings ?? []
  const totalPorts  = subdomains.reduce((acc, s) => acc + (s.ports?.length ?? 0), 0)

  const critHighVulns = vulns.filter(v => ['critical','high'].includes((v.severity || '').toLowerCase()))

  const tabs = [
    { id: 'overview',   label: 'Overview' },
    { id: 'subdomains', label: 'Subdomains', count: subdomains.length },
    { id: 'gallery',    label: 'Gallery',    count: subdomains.filter(s => s.screenshot_path).length },
    { id: 'ports',      label: 'Ports',      count: totalPorts },
    { id: 'secrets',    label: 'Secrets',    count: secrets.length },
    { id: 'endpoints',  label: 'Endpoints',  count: endpoints.length },
    { id: 'takeover',   label: 'Takeover',   count: takeovers.length },
    {
      id: 'vulns',
      label: 'Vulns',
      count: vulns.length,
      danger: critHighVulns.length > 0,
    },
    { id: 'ai',         label: 'AI Summary' },
  ]

  // ── Loading / Error ───────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <DisclaimerBanner />
        <div className="text-center space-y-4">
          <Spinner size="lg" />
          <p className="text-[#888888] text-sm font-mono">Loading scan data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <DisclaimerBanner />
        <div className="text-center space-y-4 max-w-sm">
          <div className="text-5xl">💀</div>
          <p className="text-[#ff4444] font-semibold">{error}</p>
          <Link to="/" className="btn-ghost inline-flex">← Back to Home</Link>
        </div>
      </div>
    )
  }

  if (!scan) return null

  const status    = scan.status ?? 'queued'
  const domain    = scan.domain ?? scan.target ?? id
  const createdAt = scan.created_at ?? scan.createdAt
  const doneAt    = scan.completed_at ?? scan.finished_at ?? scan.updated_at

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <DisclaimerBanner />

      <div className="max-w-7xl mx-auto px-4 pt-14 pb-12">

        {/* ── Top Bar ──────────────────────────────────────────── */}
        <header className="pt-8 pb-4 animate-fade-in">
          <div className="flex items-start justify-between gap-4 flex-wrap mb-2">
            {/* Left: back, domain, status */}
            <div className="flex items-center gap-4 flex-wrap min-w-0">
              <Link
                to="/"
                className="flex-shrink-0 text-[#555555] hover:text-[#00ff88] transition-colors p-1 -ml-1"
                title="Back to home"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </Link>

              <h1
                className="font-mono text-2xl md:text-3xl font-bold text-white truncate"
                style={{ textShadow: '0 0 20px rgba(255,255,255,0.08)' }}
              >
                {domain}
              </h1>

              <StatusBadge status={status} dot />
            </div>

            {/* Right: export buttons */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {/* PDF Report button */}
              <button
                onClick={handlePdfDownload}
                disabled={pdfLoading || status !== 'complete'}
                className="flex items-center gap-2 px-3 py-2 rounded text-xs font-semibold transition-all border disabled:opacity-40 disabled:cursor-not-allowed"
                style={{
                  background: pdfLoading ? 'transparent' : 'rgba(255,80,0,0.1)',
                  borderColor: 'rgba(255,80,0,0.4)',
                  color: '#ff6622',
                }}
                title={status !== 'complete' ? 'Available when scan is complete' : 'Download PDF Report'}
              >
                {pdfLoading ? (
                  <span className="flex items-center gap-2">
                    <Spinner size="sm" color="#ff6622" />
                    Generating...
                  </span>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    PDF REPORT
                  </>
                )}
              </button>

              {/* JSON Export button */}
              <button
                onClick={handleExport}
                disabled={exportLoading}
                className="btn-ghost flex-shrink-0"
              >
                {exportLoading ? (
                  <span className="flex items-center gap-2">
                    <Spinner size="sm" color="#888888" />
                    Exporting...
                  </span>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    EXPORT JSON
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Timestamps */}
          <div className="flex gap-6 text-xs text-[#555555] font-mono ml-9 flex-wrap">
            <span>Created: <span className="text-[#888888]">{formatDate(createdAt)}</span></span>
            {doneAt && (
              <span>Completed: <span className="text-[#888888]">{formatDate(doneAt)}</span></span>
            )}
            <span className="text-[#333333]">ID: {scan.id ?? scan._id ?? id}</span>
          </div>
        </header>

        {/* ── Pipeline Progress ─────────────────────────────────── */}
        <div className="card px-4 py-2 mb-6">
          <PipelineProgress
            currentStage={scan.current_stage ?? scan.stage}
            status={status}
          />
        </div>

        {/* ── Tab View ─────────────────────────────────────────── */}
        <div className="card p-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <TabView tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab}>
            {activeTab === 'overview'   && <OverviewTab   scan={scan} />}
            {activeTab === 'subdomains' && <SubdomainsTab subdomains={subdomains} scanId={id} />}
            {activeTab === 'gallery'    && <GalleryTab    subdomains={subdomains} scanId={id} />}
            {activeTab === 'ports'      && <PortsTab      subdomains={subdomains} />}
            {activeTab === 'secrets'    && <SecretsTab    secrets={secrets} />}
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

      </div>
    </div>
  )
}
