<div align="center">

<img src="https://img.shields.io/badge/version-2.0.0-00ff88?style=for-the-badge&labelColor=0a0a0a" />
<img src="https://img.shields.io/badge/license-MIT-00ff88?style=for-the-badge&labelColor=0a0a0a" />
<img src="https://img.shields.io/badge/docker-ready-00ff88?style=for-the-badge&logo=docker&logoColor=white&labelColor=0a0a0a" />
<img src="https://img.shields.io/badge/python-3.11-00ff88?style=for-the-badge&logo=python&logoColor=white&labelColor=0a0a0a" />
<img src="https://img.shields.io/badge/react-18-00ff88?style=for-the-badge&logo=react&logoColor=white&labelColor=0a0a0a" />

<br /><br />

```
█████╗ ██████╗  ██████╗ ██╗   ██╗███████╗
██╔══██╗██╔══██╗██╔════╝ ██║   ██║██╔════╝
███████║██████╔╝██║  ███╗██║   ██║███████╗
██╔══██║██╔══██╗██║   ██║██║   ██║╚════██║
██║  ██║██║  ██║╚██████╔╝╚██████╔╝███████║
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝

███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
```

# A hundred eyes on your attack surface.

**Argus-Sentinel** is a fully automated offensive reconnaissance platform that replicates the exact workflow professional bug bounty hunters and penetration testers use — in a single button click.

Drop in a domain. Walk away. Come back to a complete attack surface map.

<br />

[**Live Demo**](#) · [**Report a Bug**](https://github.com/Ayaan1911/Argus-Sentinel/issues) · [**Request Feature**](https://github.com/Ayaan1911/Argus-Sentinel/issues) · [**Documentation**](#architecture)

<br />

![Argus-Sentinel Dashboard](https://raw.githubusercontent.com/Ayaan1911/Argus-Sentinel/main/docs/dashboard-preview.png)

</div>

---

## Why Argus-Sentinel?

Most recon tools do one thing. You run subfinder, pipe it to httpx, run nmap, manually dig through JS files, check for secrets, look for takeovers — and you do this for every single target, every single time.

**Argus-Sentinel automates the entire chain.**

```
You type a domain.
It finds everything they didn't want you to find.
```

This isn't a script wrapper. It's a full-stack distributed intelligence platform — async task orchestration, real-time dashboard, AI-powered attack surface analysis, PDF pentest reports, and vulnerability scanning with 5000+ Nuclei templates — running in a single `docker compose up`.

---

## What it finds

| Module | What it discovers |
|--------|-------------------|
| 🌐 **Subdomain Enumeration** | Every subdomain via cert transparency, DNS brute-force, public APIs |
| 💓 **Live Host Detection** | Which hosts are actually alive, their status codes, tech stack |
| 🔌 **Port Scanning** | Open ports, running services, version fingerprinting |
| 📸 **Screenshots** | Visual recon — automatic screenshots of every live host |
| 📜 **JS Extraction** | Every JavaScript file served by every live host |
| 🔑 **Secret Detection** | AWS keys, JWTs, API tokens, private keys leaked in JS |
| 🗺️ **Endpoint Mining** | Hidden API routes, admin paths, GraphQL endpoints in JS bundles |
| ⚠️ **Takeover Detection** | Dangling CNAMEs pointing to unclaimed cloud resources |
| 🎯 **Vulnerability Scanning** | 5000+ Nuclei templates — CVEs, misconfigs, exposed panels |
| 🤖 **AI Analysis** | GPT-4o-mini summarizes findings as a senior bug bounty hunter would |
| 📄 **PDF Reports** | Professional pentest-grade export you can hand to a client |

---

## Real results on real targets

```
Target: hackthebox.com

  Subdomains found:     100
  Live hosts:            39
  Open ports:           116
  JS endpoints:         842
  Secrets detected:       5
  Vulnerabilities:       12
  Takeover risks:         0
  Screenshots:           39

  Time elapsed: 8m 42s
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  React + Vite + Tailwind  (port 5173)                                │
│  Real-time polling · 10-stage pipeline progress · 9 result tabs      │
└───────────────────────────┬──────────────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼──────────────────────────────────────────┐
│  FastAPI  (port 8000)                                                │
│  POST /api/scan → create job → enqueue                               │
│  GET  /api/scan/{id} → stream results as they arrive                 │
│  GET  /api/scan/{id}/report/pdf → download pentest report            │
└──────────────┬────────────────────────────┬─────────────────────────┘
               │ publish                    │ read/write
      ┌────────▼──────────┐     ┌───────────▼──────────────┐
      │  Redis  (broker)  │     │  PostgreSQL 15  (state)   │
      └────────┬──────────┘     └──────────────────────────┘
               │ consume
      ┌────────▼──────────────────────────────────────────────────────┐
      │  Celery Worker                                                 │
      │                                                                │
      │  1  Subdomain Enum    subfinder + DNS brute-force             │
      │       ↓                                                        │
      │  2  Live Hosts        /root/go/bin/httpx                      │
      │       ↓                                                        │
      │  3  Screenshots       /root/go/bin/gowitness                  │
      │       ↓                                                        │
      │  4  Port Scan         nmap -T4 --top-ports 1000               │
      │       ↓                                                        │
      │  5  JS Extraction     BeautifulSoup + HTTP fetch               │
      │       ↓                                                        │
      │  6  Secret Detection  24 regex pattern families                │
      │       ↓                                                        │
      │  7  Endpoint Mining   API path extraction from JS bundles      │
      │       ↓                                                        │
      │  8  Takeover Check    CNAME + cloud fingerprint matching       │
      │       ↓                                                        │
      │  9  Nuclei Scan       5000+ vuln templates (critical→medium)  │
      │       ↓                                                        │
      │  10 AI Summary        OpenRouter GPT-4o-mini analysis          │
      └────────────────────────────────────────────────────────────────┘
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite 5, Tailwind CSS 3 |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2 |
| Task Queue | Celery 5, Redis 7 |
| Database | PostgreSQL 15, Alembic migrations |
| Recon | subfinder, httpx, nmap, gowitness, nuclei |
| AI | OpenRouter (GPT-4o-mini) |
| Reports | WeasyPrint, Jinja2 |
| Runtime | Docker, Docker Compose |

---

## Getting started

### Prerequisites

- [Docker](https://www.docker.com/get-started) v24+
- [Docker Compose](https://docs.docker.com/compose/) v2.20+
- An [OpenRouter](https://openrouter.ai) API key *(optional — AI Summary only)*

### Installation

```bash
# 1. Clone
git clone https://github.com/Ayaan1911/Argus-Sentinel.git
cd Argus-Sentinel

# 2. Configure
cp .env.example .env
# Edit .env — add your OPENROUTER_API_KEY (optional)

# 3. Launch
docker compose up --build
```

> First build takes **8–12 minutes** — Go compiles subfinder, httpx, nuclei, and gowitness from source inside Docker. Subsequent builds use cache and start in seconds.

### Access

| Service | URL |
|---------|-----|
| 🖥️ Dashboard | http://localhost:5173 |
| 📡 API | http://localhost:8000 |
| 📖 API Docs (Swagger) | http://localhost:8000/docs |

---

## Usage

### Run a scan

1. Open `http://localhost:5173`
2. Enter a target domain you own or have permission to test
3. Click **INITIATE SCAN**
4. Watch the 10-stage pipeline execute in real time
5. When complete — download the PDF report

### API

```bash
# Start a scan
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com"}'

# Poll results
curl http://localhost:8000/api/scan/{scan_id}

# Download PDF report
curl http://localhost:8000/api/scan/{scan_id}/report/pdf \
  --output report.pdf

# Export JSON
curl http://localhost:8000/api/scan/{scan_id}/export
```

All responses follow the envelope format:
```json
{
  "success": true,
  "data": {},
  "error": null
}
```

---

## Secret detection patterns

| Pattern | Severity | Confidence |
|---------|----------|------------|
| AWS Access Key (`AKIA...`) | 🔴 Critical | 95% |
| Private Keys (RSA/EC/DSA) | 🔴 Critical | 99% |
| AWS Secret Key | 🔴 Critical | 95% |
| GitHub Token (`ghp_...`) | 🟠 High | 90% |
| Stripe Secret Key (`sk_live_...`) | 🟠 High | 92% |
| Hardcoded Password | 🟠 High | 65% |
| JWT Token | 🟡 Medium | 75% |
| Google API Key (`AIza...`) | 🟡 Medium | 80% |
| Slack Token (`xoxb-...`) | 🟡 Medium | 88% |
| Generic API Key | 🟡 Medium | 60% |
| Stripe Publishable Key | 🔵 Low | 90% |
| OAuth Client ID | ⚪ Info | 70% |

---

## Project structure

```
argus-sentinel/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS
│   │   ├── models.py            # SQLAlchemy ORM models (7 tables)
│   │   ├── schemas.py           # Pydantic response schemas
│   │   ├── database.py          # DB engine + session factory
│   │   ├── routes/
│   │   │   └── scans.py         # All API route handlers
│   │   └── reports/
│   │       ├── generator.py     # PDF generation logic
│   │       └── template.html    # Jinja2 pentest report template
│   ├── tasks/
│   │   ├── celery_app.py        # Celery instance + config
│   │   ├── pipeline.py          # Main scan orchestrator
│   │   └── modules/
│   │       ├── subdomain_enum.py
│   │       ├── live_host_check.py
│   │       ├── screenshot_capture.py
│   │       ├── port_scan.py
│   │       ├── js_extractor.py
│   │       ├── secret_detector.py
│   │       ├── endpoint_miner.py
│   │       ├── takeover_check.py
│   │       ├── nuclei_scan.py
│   │       └── ai_summary.py
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── start.sh
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── ScanDetail.jsx   # 9 tabs, live polling, gallery
│   │   ├── components/
│   │   │   ├── MetricCard.jsx
│   │   │   ├── StatusBadge.jsx
│   │   │   ├── TabView.jsx
│   │   │   └── PipelineProgress.jsx
│   │   └── api/
│   │       └── client.js
│   ├── package.json
│   └── Dockerfile
├── wordlists/
│   └── subdomains-top1000.txt
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## Roadmap

- [x] Subdomain enumeration (subfinder + brute-force)
- [x] Live host detection (httpx)
- [x] Port scanning (nmap)
- [x] JS extraction + secret detection
- [x] Endpoint mining
- [x] Subdomain takeover detection
- [x] AI-powered attack surface summary
- [x] Screenshot capture (gowitness)
- [x] Nuclei vulnerability scanning
- [x] PDF pentest report export
- [x] Secret severity + confidence scoring
- [ ] Continuous monitoring (scheduled rescans + diff alerts)
- [ ] Discord / Slack / Telegram notifications
- [ ] Multi-user support with workspaces
- [ ] Distributed workers across multiple VPS
- [ ] Custom Nuclei template upload
- [ ] CVSS scoring per vulnerability
- [ ] Kubernetes deployment manifests

---

## Safe testing targets

Only use Argus-Sentinel against domains you own or have explicit written authorization to test. Here are legal practice targets:

| Target | Notes |
|--------|-------|
| `scanme.nmap.org` | Nmap's official test host |
| `testphp.vulnweb.com` | Acunetix intentionally vulnerable app |
| Your own domain | Always safe |
| HackTheBox / TryHackMe labs | Within lab scope |

---

## Contributing

Contributions are what make the open source community great. Any contribution you make is **hugely appreciated**.

```bash
# Fork → Branch → Commit → Push → PR

git checkout -b feature/your-feature
git commit -m 'feat: add your feature'
git push origin feature/your-feature
# Open a Pull Request
```

Ideas for contributions: new Nuclei template categories, additional secret patterns, new export formats, UI improvements, performance optimizations.

---

## Legal disclaimer

> Argus-Sentinel is intended for **authorized security testing only**.
>
> Only scan domains you own or have **explicit written permission** to test. Unauthorized scanning may violate the Computer Fraud and Abuse Act (CFAA), the UK Computer Misuse Act, and equivalent laws in your jurisdiction. The authors accept no liability for misuse.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">

Built by [Mohammad Ayaan](https://github.com/Ayaan1911) · Powered by [ProjectDiscovery](https://projectdiscovery.io) toolchain

*"The eye that sees everything is the eye that finds everything."*

⭐ Star this repo if Argus-Sentinel helped you find something interesting.

</div>

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ for the security community. Remember: with great power comes great responsibility.*
