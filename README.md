# Argus-Sentinel 🔍

> **A hundred eyes on your attack surface.**

Argus-Sentinel is an automated cybersecurity reconnaissance tool designed for bug bounty hunters and security professionals. It takes a target domain and runs a comprehensive 8-stage recon pipeline — subdomain enumeration, live host detection, port scanning, JS file extraction, secret detection, endpoint mining, subdomain takeover checks, and AI-powered analysis — all presented in a sleek real-time dashboard.

**GitHub Repository**: [https://github.com/Ayaan1911/Argus-Sentinel](https://github.com/Ayaan1911/Argus-Sentinel)

---

## ⚠️ Legal Disclaimer

> **Argus-Sentinel is intended for authorized security testing only.**
>
> Only scan domains you own or have explicit written permission to test. Unauthorized scanning may violate computer crime laws including the Computer Fraud and Abuse Act (CFAA), the UK Computer Misuse Act, and similar legislation worldwide. The authors of Argus-Sentinel are not responsible for any misuse or damage caused by this tool.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Browser: React + Vite + Tailwind (port 5173)                               │
│  Home → Submit domain → Poll /api/scan/{id} every 3s → Real-time dashboard  │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │ HTTP REST API
┌────────────────────────────▼────────────────────────────────────────────────┐
│  FastAPI (port 8000)                                                         │
│  POST /api/scan → create Scan row → enqueue Celery task                     │
│  GET  /api/scan/{id} → read results from PostgreSQL                         │
│  GET  /api/scans, DELETE /api/scan/{id}, GET /api/scan/{id}/export          │
└───────────┬────────────────────────────────────┬────────────────────────────┘
            │ publish task                        │ read/write
   ┌────────▼──────────┐              ┌───────────▼──────────────┐
   │  Redis (broker)   │              │  PostgreSQL 15 (state)    │
   └────────┬──────────┘              └──────────────────────────┘
            │ consume
   ┌────────▼──────────────────────────────────────────────────────────┐
   │  Celery Worker (same Docker image as API)                          │
   │                                                                    │
   │  Stage 1: Subdomain Enumeration (subfinder + DNS brute-force)      │
   │     ↓                                                              │
   │  Stage 2: Live Host Detection (httpx)                              │
   │     ↓                                                              │
   │  Stage 3: Port Scanning (nmap --top-ports 1000)                   │
   │     ↓                                                              │
   │  Stage 4: JS File Extraction (HTML parsing + JS fetch)            │
   │     ↓                                                              │
   │  Stage 5: Secret Detection (regex patterns on JS content)         │
   │     ↓                                                              │
   │  Stage 6: Endpoint Mining (URL/path extraction from JS)           │
   │     ↓                                                              │
   │  Stage 7: Subdomain Takeover Check (CNAME + fingerprint match)    │
   │     ↓                                                              │
   │  Stage 8: AI Summary (OpenRouter GPT-4o-mini analysis)            │
   └───────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v24+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.20+)
- An [OpenRouter API key](https://openrouter.ai/keys) (optional, for AI Summary)

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Ayaan1911/Argus-Sentinel.git
cd Argus-Sentinel
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your OpenRouter API key:

```env
OPENROUTER_API_KEY=your_key_here
DATABASE_URL=postgresql://postgres:password@db:5432/argus
REDIS_URL=redis://redis:6379/0
```

### 3. Build & Start

```bash
docker compose up --build
```

First build will take 5–10 minutes (installs Go, subfinder, httpx, nmap).

### 4. Access the Dashboard

| Service   | URL                          |
|-----------|------------------------------|
| Frontend  | http://localhost:5173        |
| API Docs  | http://localhost:8000/docs   |
| API Root  | http://localhost:8000        |

---

## Usage

### Submit a Scan

1. Open **http://localhost:5173** in your browser
2. Enter a target domain (e.g., `example.com`) in the input field
3. Click **INITIATE SCAN**
4. You'll be redirected to the scan detail page

### Read Results

The scan detail page shows:
- **Pipeline Progress Bar** — real-time stage updates
- **Overview** — metric cards for all finding categories
- **Subdomains** — table of all discovered subdomains
- **Ports** — open ports grouped by host
- **Secrets** — potential secrets found in JS files
- **Endpoints** — API paths and URLs mined from JS
- **Takeover Risks** — potential subdomain takeover vulnerabilities
- **AI Summary** — GPT-4o-mini analysis of all findings

### Export Results

Click **EXPORT JSON** on the scan detail page, or call:

```bash
curl http://localhost:8000/api/scan/{scan_id}/export
```

---

## Pipeline Module Breakdown

| # | Module | Tool/Method | Output |
|---|--------|-------------|--------|
| 1 | **Subdomain Enumeration** | `subfinder` + DNS brute-force (1000 wordlist) | Subdomains table |
| 2 | **Live Host Detection** | `httpx` — status codes, titles, tech detection | Updates subdomains (is_alive, status_code, title, technologies) |
| 3 | **Port Scanning** | `nmap -T4 --top-ports 1000 -sV` | Ports table per live host |
| 4 | **JS File Extraction** | BeautifulSoup HTML parsing + HTTP fetch | JS file content in memory |
| 5 | **Secret Detection** | Regex patterns (AWS, JWT, API keys, private keys, etc.) | Secrets table |
| 6 | **Endpoint Mining** | Regex on JS content for API paths and full URLs | Endpoints table |
| 7 | **Takeover Check** | DNS CNAME resolution + fingerprint matching | Takeover risks table |
| 8 | **AI Summary** | OpenRouter GPT-4o-mini — structured bug bounty analysis | AI Summary (markdown) |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scan` | Start a new scan `{"domain": "example.com"}` |
| `GET` | `/api/scan/{id}` | Get scan status + all results |
| `GET` | `/api/scans` | List all scans |
| `DELETE` | `/api/scan/{id}` | Delete a scan |
| `GET` | `/api/scan/{id}/export` | Export full results as JSON |
| `POST` | `/api/scan/{id}/regenerate-summary` | Re-run AI summary |

All responses use the envelope format:
```json
{
  "success": true,
  "data": {},
  "error": null
}
```

---

## Project Structure

```
argus-sentinel/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS + router
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── schemas.py           # Pydantic response schemas
│   │   ├── database.py          # DB engine + session
│   │   └── routes/
│   │       └── scans.py         # API route handlers
│   ├── tasks/
│   │   ├── celery_app.py        # Celery instance
│   │   ├── pipeline.py          # Main scan task + stage runner
│   │   └── modules/
│   │       ├── subdomain_enum.py
│   │       ├── live_host_check.py
│   │       ├── port_scan.py
│   │       ├── js_extractor.py
│   │       ├── secret_detector.py
│   │       ├── endpoint_miner.py
│   │       ├── takeover_check.py
│   │       └── ai_summary.py
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── start.sh
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── ScanDetail.jsx
│   │   ├── components/
│   │   │   ├── MetricCard.jsx
│   │   │   ├── StatusBadge.jsx
│   │   │   ├── TabView.jsx
│   │   │   └── PipelineProgress.jsx
│   │   ├── api/
│   │   │   └── client.js
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── wordlists/
│   └── subdomains-top1000.txt
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite 5, Tailwind CSS 3 |
| Backend API | FastAPI, Python 3.11 |
| Task Queue | Celery 5, Redis 7 |
| Database | PostgreSQL 15, SQLAlchemy 2, Alembic |
| Recon Tools | subfinder (Go), httpx (Go), nmap |
| AI | OpenRouter API (GPT-4o-mini) |
| Container | Docker, Docker Compose |

---

## Secret Detection Patterns

| Pattern | Severity |
|---------|----------|
| AWS Access Key (`AKIA...`) | 🔴 Critical |
| Private Keys (RSA/EC/DSA) | 🔴 Critical |
| JWT Tokens | 🟠 High |
| Generic API Keys | 🟠 High |
| GitHub Tokens (`ghp_...`) | 🟡 Medium |
| Slack Tokens (`xox...`) | 🟡 Medium |
| Google API Keys (`AIza...`) | 🟡 Medium |
| Stripe Keys (`sk_live_...`) | 🟡 Medium |
| Hardcoded Passwords | 🟡 Medium |
| Bearer Tokens | 🟢 Low |

---

## Troubleshooting

**Build takes too long?**
The first build installs Go + subfinder + httpx which can take 5–10 minutes. Subsequent builds use Docker cache and are much faster.

**subfinder/httpx not working?**
These tools require network access to query public APIs and DNS resolvers. Ensure your Docker container has internet access.

**AI Summary not generating?**
Ensure `OPENROUTER_API_KEY` is set in your `.env` file. Without it, a placeholder message is shown. Click "Regenerate Summary" after adding the key.

**Port scan timing out?**
Nmap is capped at 50 live hosts and has a 120s timeout per host. For large scans, this stage may take several minutes.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ for the security community. Remember: with great power comes great responsibility.*
