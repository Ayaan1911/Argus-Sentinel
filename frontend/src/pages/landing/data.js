// Real content only — every value here was pulled from an actual scan or
// an actual file in this repo, not invented for marketing copy. Sources are
// noted inline so a future session can re-verify instead of trusting this
// blindly (per this repo's own rule about treating past notes as snapshots,
// not ground truth).

// Pipeline order + one-line purpose per stage, matching the real sequential
// pipeline in backend/app/tasks/scan_tasks.py::_run_pipeline: subfinder's
// output feeds httpx, httpx's confirmed-live hosts feed nmap, and nmap's
// scan targets (resolved to httpx's live URLs where possible) feed nuclei.
export const PIPELINE_STAGES = [
  {
    name: 'subfinder',
    role: 'Discover',
    desc: 'Passive subdomain enumeration. Maps the attack surface before anything is touched directly.',
  },
  {
    name: 'httpx',
    role: 'Confirm',
    desc: "Probes every discovered host to see what's actually alive, and fingerprints the technology running on it.",
  },
  {
    name: 'nmap',
    role: 'Scan',
    desc: 'Port scans the live hosts and identifies the service and version behind each open port.',
  },
  {
    name: 'nuclei',
    role: 'Detect',
    desc: "Runs template-based vulnerability checks against what's actually live, using the real ports and paths httpx already confirmed.",
  },
];

// A real finding from an actual scan (backend/app/engines/reasoning.py
// output, captured via the live API — see notes.md for the session this was
// pulled in). The target it came from isn't shown here; the score and
// reasoning are exactly what Argus produced. This is the only finding in
// this database whose breakdown has more than a base score, i.e. the only
// real example where a correlation modifier actually fired.
export const EXAMPLE_FINDING = {
  title: 'Port 8080/tcp: tcpwrapped',
  type: 'port',
  severity: 'low',
  final_risk_score: 4.0,
  confidence: 1.0,
  technical_impact:
    'An open port was detected but the service running on it could not be conclusively identified. This may be due to a TCP wrapper, non-standard service, or limited probe response. The port represents an entry point that warrants further manual investigation.',
  reasoning_breakdown: [
    { label: 'Base Score', modifier: 2.0, reason: 'Initial base score derived from finding type and intelligence data.' },
    { label: 'Internet Facing', modifier: 2.0, reason: 'Service is exposed to the public internet.' },
  ],
};

// A real scan-history diff — two actual completed scans of the bundled
// juice-shop target, ~17 hours apart (2026-09-14 -> 2026-09-15). Fetched
// live from GET /scans/{id}/diff. No CHANGED example exists in this
// database yet (a finding's score only moves between scans if something
// about its context actually changed, which hasn't happened for this
// target) — described in prose in Differentiators.jsx instead of faked here.
export const DIFF_EXAMPLE = {
  summary: { new: 9, resolved: 3, changed: 0, unchanged: 4 },
  new_findings: [
    { title: 'Public Swagger API - Detect', type: 'vulnerability', severity: 'informational' },
    { title: 'HTTP Missing Security Headers', type: 'vulnerability', severity: 'informational' },
  ],
  resolved_findings: [
    { title: 'Wappalyzer Technology Detection', type: 'vulnerability', severity: 'informational' },
    { title: 'FingerprintHub Technology Fingerprint', type: 'vulnerability', severity: 'informational' },
  ],
};

// From GET /health -> intelligence_library, the same live loader count the
// app itself reports. Kept as one named export instead of a hardcoded "51"
// scattered through copy, so this file is the one place to update if the
// library's real count ever changes.
export const INTELLIGENCE_COUNTS = { services: 25, technologies: 12, vulnerabilities: 14 };
export const INTELLIGENCE_TOTAL =
  INTELLIGENCE_COUNTS.services + INTELLIGENCE_COUNTS.technologies + INTELLIGENCE_COUNTS.vulnerabilities;

export const GITHUB_URL = 'https://github.com/Ayaan1911/Argus-Sentinel';
export const INTELLIGENCE_CONTRIBUTING_URL = `${GITHUB_URL}/blob/main/argus-intelligence/CONTRIBUTING.md`;

// Single source of truth for both landing-page CTAs that touch the app
// (Nav's "Launch App" and Hero's "Try the Demo"), so the two can't drift
// out of sync about what deployment mode this build is running in.
//
// This frontend has no per-visitor login — every deployment bakes one fixed
// VITE_API_KEY into the JS bundle at build time (see frontend/api/client.js),
// so "/dashboard" already works for whoever can reach this origin, in every
// mode this repo actually supports:
//   - VITE_DEMO_MODE=true (the public demo build): the baked-in key is the
//     public DEMO_API_KEY, and DEMO_MODE also locks the target to juice-shop
//     app-wide (see Layout.jsx/NewScan.jsx) — so /dashboard already IS the
//     locked demo, from either CTA.
//   - VITE_DEMO_MODE=false (a self-hosted build): the baked-in key is
//     whatever the self-hoster generated for themselves, and /dashboard is
//     their real, unrestricted instance — correct for their own landing page.
// There's no third "marketing-only, no backend configured" deployment in
// this repo's docker-compose files, so /dashboard doesn't need to branch.
export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

// "Try the Demo" points at the locked PUBLIC demo instance once it's
// deployed (see DEMO_DEPLOYMENT.md — no live URL exists yet, that file only
// documents how to stand one up). If this exact build IS that demo
// deployment, /dashboard already is the locked demo, so link there directly
// instead of an external placeholder.
// PLACEHOLDER — replace once DEMO_DEPLOYMENT.md has actually been run
// against a real host and a real domain exists.
export const PLACEHOLDER_DEMO_URL = 'https://demo.argus-sentinel.dev';
export const DEMO_URL = DEMO_MODE ? '/dashboard' : PLACEHOLDER_DEMO_URL;

// Whether the "Try the Demo" hero CTA should render at all. On a
// self-hosted (non-demo) build there's no live public demo to send visitors
// to but the placeholder domain, and the self-hoster's own "Launch App"
// link already offers full, unrestricted access to this exact instance —
// showing a second CTA that points at an unrelated, unresolving external
// domain would be actively confusing rather than merely redundant. Both
// CTAs are kept (not hidden) in demo mode, where they correctly point at
// the same real, working destination.
export const SHOW_DEMO_CTA = DEMO_MODE;
