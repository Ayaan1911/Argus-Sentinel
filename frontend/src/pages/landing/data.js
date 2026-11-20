// The examples below were captured from completed scans. They are evidence
// samples for the landing page, not current results from the visitor's app.
export const PIPELINE_STAGES = [
  {
    name: 'subfinder',
    role: 'Discover',
    desc: 'Passive subdomain enumeration maps the attack surface before anything is touched directly.',
  },
  {
    name: 'httpx',
    role: 'Confirm',
    desc: 'Probes discovered hosts to find live services and fingerprint their technology.',
  },
  {
    name: 'nmap',
    role: 'Scan',
    desc: 'Inspects live hosts for open ports, services, and versions.',
  },
  {
    name: 'nuclei',
    role: 'Detect',
    desc: 'Checks confirmed live services with vulnerability templates.',
  },
];

// Recorded finding from a real scan. The target is withheld.
export const EXAMPLE_FINDING = {
  title: 'Port 8080/tcp: tcpwrapped',
  type: 'port',
  severity: 'low',
  final_risk_score: 4.0,
  technical_impact:
    'An open port was detected but the service running on it could not be conclusively identified. This may be due to a TCP wrapper, non-standard service, or limited probe response. The port represents an entry point that warrants further manual investigation.',
  reasoning_breakdown: [
    { label: 'Base Score', modifier: 2.0 },
    { label: 'Internet Facing', modifier: 2.0 },
  ],
};

// Recorded diff from two completed Juice Shop scans in September 2026.
export const DIFF_EXAMPLE = {
  summary: { new: 9, resolved: 3, unchanged: 4 },
  new_findings: [{ title: 'Public Swagger API - Detect' }],
  resolved_findings: [{ title: 'Wappalyzer Technology Detection' }],
};

// Count verified against the intelligence loader when this example was made.
export const INTELLIGENCE_TOTAL = 51;
export const GITHUB_URL = 'https://github.com/Ayaan1911/Argus-Sentinel';
export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';
