# Argus Sentinel

AI-Powered Cybersecurity Reasoning Engine — turns raw scan output into prioritized, explainable findings with audience-aware guidance.

---

## The Core Idea

Most security tools answer: **"What did you find?"**

Argus answers: **"What does it mean, why does it matter, and what should you do next?"**

The scanners (Subfinder, Httpx, Nmap, Nuclei) are inputs. The intelligence and reasoning layer is the product. Any tool can wrap a scanner in a UI. What Argus builds — the knowledge base, the deterministic reasoning engine, the correlation logic, and the audience-aware guidance — is what makes findings actually useful.

---

## Architecture

```
Discovery → Intelligence → Reasoning → Guidance → Learning
```

**Discovery** — Subfinder enumerates subdomains, Httpx probes live hosts, Nmap maps ports and services, Nuclei runs vulnerability templates.

**Intelligence** — Raw findings are matched against the Argus Intelligence Library: a structured knowledge base of services, technologies, and vulnerability classes. A port 22 finding becomes a contextualized SSH exposure with known attack patterns and real-world incident context.

**Reasoning** — A deterministic engine calculates risk scores from explicit modifiers (exposure, misconfiguration, known CVEs, correlation). Every score shows its work — no black-box outputs.

**Guidance** — Every finding produces a prioritized action list specific to what was actually found, not generic advice.

**Learning** — The same finding is explained differently based on the selected audience: Student, Developer, Bug Bounty Hunter, or Security Professional.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Python 3.11 |
| Task queue | Celery + Redis |
| Database | PostgreSQL 15 (SQLAlchemy async) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Scanners | Subfinder, Httpx, Nmap, Nuclei v3 |
| Containers | Docker Compose |

---

## Setup

```bash
git clone https://github.com/Ayaan1911/Argus-Sentinel
cd Argus-Sentinel

cp .env.example .env
# Edit .env if you need non-default credentials

docker compose up --build
```

Services after startup:

- Frontend: http://localhost:5173
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- OWASP Juice Shop (local scan target): http://localhost:3000

Run a scan against Juice Shop to verify the full pipeline end-to-end:

```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Content-Type: application/json" \
  -d '{"target": "http://juice-shop:3000"}'
```

---

## Screenshots

<!-- Screenshots and GIFs to be added -->

---

## Verified Behavior

Tested against OWASP Juice Shop running in the same Docker network:

- Nuclei v3.3.9 binary at `/usr/local/bin/nuclei` — matches hardcoded path in scanner config
- Templates loaded: 2898 across `exposure`, `misconfig`, `tech` tags
- Scan result (Juice Shop): 13 findings including Public Swagger API exposure, missing security headers, tech fingerprints (FingerprintHub, Wappalyzer), and Prometheus metrics endpoint
- Each finding carries a `reasoning_breakdown` array with labeled score modifiers
- Audience guidance populates for findings matched against the Intelligence Library

---

## Known Limitations

- **WAF-hardened targets** like github.com intentionally return fewer findings. Nuclei is rate-limited to 50 req/s and backs off on 429s — this is by design, not a bug.
- **Network reachability** depends on host environment. Scanning external targets requires the worker container to have outbound internet access. Internal targets (like Juice Shop) must be on the same Docker network.
- **Intelligence Library coverage** is V1 scope: 5 services (SSH, HTTP, HTTPS, MySQL, Redis), 4 technologies (Apache, Nginx, Tomcat, WordPress), 5 vulnerability classes (SQLi, XSS, SSRF, IDOR, RCE). Findings outside this coverage get base reasoning only — `audience_guidance` will be empty for unmatched template IDs.
- **No authentication** on the API in V1. Do not expose port 8000 publicly.

---

## License

MIT — see [LICENSE](LICENSE) for details.
