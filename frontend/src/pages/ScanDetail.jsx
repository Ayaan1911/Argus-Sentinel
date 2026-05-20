import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { getScan, exportScan, regenerateSummary } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import PipelineProgress from '../components/PipelineProgress'
import MetricCard from '../components/MetricCard'
import TabView from '../components/TabView'

// ── Constants ─────────────────────────────────────────────────────────────────

const DANGEROUS_PORTS = new Set([21, 22, 23, 25, 53, 110, 135, 139, 143, 445, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017])
const WEB_PORTS       = new Set([80, 443])

const SECRET_SEVERITY = {
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
  const exact = SECRET_SEVERITY[lower]
  if (exact) return exact
  for (const [k, v] of Object.entries(SECRET_SEVERITY)) {
    if (lower.includes(k) || k.includes(lower)) return v
  }
  return { label: type, color: 'bg-[#1a1a1a] text-[#888888] border-[#333333]' }
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
  github:    '🐙',
  heroku:    '💜',
  aws:       '☁️',
  azure:     '🔷',
  gcp:       '🌐',
  google:    '🌐',
  shopify:   '🛍️',
  fastly:    '⚡',
  pantheon:  '🐍',
  bitbucket: '🪣',
  gitlab:    '🦊',
  sendgrid:  '📧',
  zendesk:   '💬',
  unbounce:  '📢',
  surge:     '🌊',
  default:   '⚠️',
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
    <svg
      className={`${sizes[size]} animate-spin`}
      fill="none"
      viewBox="0 0 24 24"
      style={{ color }}
    >
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

  return (
    <div className="animate-slide-up">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <MetricCard icon="🌐" label="Total Subdomains" value={subdomains.length} />
        <MetricCard icon="💓" label="Live Hosts"        value={liveHosts.length} />
        <MetricCard icon="🔌" label="Open Ports"        value={totalPorts} />
        <MetricCard
          icon="🔑"
          label="Secrets Detected"
          value={secrets.length}
          variant={secrets.length > 0 ? 'danger' : 'default'}
          subtitle={secrets.length > 0 ? 'Immediate attention required' : undefined}
        />
        <MetricCard icon="🗺️" label="Endpoints Found"  value={endpoints.length} />
        <MetricCard
          icon="⚠️"
          label="Takeover Risks"
          value={takeovers.length}
          variant={takeovers.length > 0 ? 'danger' : 'default'}
          subtitle={takeovers.length > 0 ? 'Subdomain takeover detected' : undefined}
        />
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

function SubdomainsTab({ subdomains = [] }) {
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
    <div className="animate-slide-up space-y-4">
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

                  return (
                    <tr key={host + i}>
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
            {/* Host header */}
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

function SecretsTab({ secrets = [] }) {
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
          </p>
          <p className="text-[#884444] text-xs mt-0.5">
            Exposed credentials found in JavaScript files. Rotate these immediately.
          </p>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Source File</th>
                <th>Value Preview</th>
                <th>Line #</th>
              </tr>
            </thead>
            <tbody>
              {secrets.map((s, i) => {
                const type    = s.secret_type ?? s.type ?? s.kind ?? 'unknown'
                const fileUrl = s.file_url ?? s.url ?? s.source ?? s.js_file ?? ''
                const value   = s.matched_value ?? s.value ?? s.secret ?? s.match ?? ''
                const lineNum = s.line_number ?? s.line ?? s.line_num ?? '—'
                const style   = getSecretStyle(type)
                const isHighRisk = style.color.includes('red')

                return (
                  <tr
                    key={i}
                    className={isHighRisk ? 'bg-[rgba(255,68,68,0.04)] hover:bg-[rgba(255,68,68,0.07)]' : ''}
                  >
                    <td>
                      <span className={`pill border text-[0.6rem] ${style.color}`}>
                        {style.label}
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
                          <span
                            className={`font-mono text-sm ${isHL ? 'text-[#00ff88]' : 'text-[#cccccc]'}`}
                          >
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

      {/* Pagination */}
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
      {/* Danger banner */}
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

// ── AI SUMMARY TAB ────────────────────────────────────────────────────────────

function AISummaryTab({ scan, onRegenerate, isRegenerating }) {
  const aiSummaryObj = scan.ai_summary
  const summary   = aiSummaryObj?.summary_text ?? scan.summary_text ?? scan.summary
  const createdAt = aiSummaryObj?.created_at ?? scan.summary_created_at ?? scan.summary_at

  return (
    <div className="animate-slide-up space-y-5">
      {/* Header row */}
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

      {/* Content */}
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
          {/* Timestamp */}
          {createdAt && (
            <p className="text-[#444444] text-xs font-mono mb-5">
              Generated {formatRelativeTime(createdAt)}
            </p>
          )}
          {/* Rendered Markdown */}
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

  // ── Export ────────────────────────────────────────────────────────────────

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

  const subdomains = scan?.subdomains ?? []
  const secrets    = scan?.secrets ?? []
  const endpoints  = scan?.endpoints ?? []
  const takeovers  = scan?.takeover_risks ?? scan?.takeovers ?? []
  const totalPorts = subdomains.reduce((acc, s) => acc + (s.ports?.length ?? 0), 0)

  const tabs = [
    { id: 'overview',   label: 'Overview' },
    { id: 'subdomains', label: 'Subdomains', count: subdomains.length },
    { id: 'ports',      label: 'Ports',      count: totalPorts },
    { id: 'secrets',    label: 'Secrets',    count: secrets.length },
    { id: 'endpoints',  label: 'Endpoints',  count: endpoints.length },
    { id: 'takeover',   label: 'Takeover',   count: takeovers.length },
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
          {/* Back + meta row */}
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

            {/* Right: export button */}
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
            {activeTab === 'subdomains' && <SubdomainsTab subdomains={subdomains} />}
            {activeTab === 'ports'      && <PortsTab      subdomains={subdomains} />}
            {activeTab === 'secrets'    && <SecretsTab    secrets={secrets} />}
            {activeTab === 'endpoints'  && <EndpointsTab  endpoints={endpoints} />}
            {activeTab === 'takeover'   && <TakeoverTab   takeovers={takeovers} />}
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
