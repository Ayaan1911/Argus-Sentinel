# Argus Sentinel

**An automated web reconnaissance tool that turns raw scanner output into risk-scored, explained findings.**

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.11-3776AB)
![React](https://img.shields.io/badge/react-18-61DAFB)
![Docker](https://img.shields.io/badge/docker-compose-2496ED)

---

A user submits a target domain; the backend runs subfinder, httpx, nmap, and nuclei against it in sequence, and a correlation/reasoning engine — backed by a 57-entry JSON intelligence library — turns the raw output into risk-scored findings with audience-specific guidance. Built for authorized testing of owned/permitted targets, with a bundled OWASP Juice Shop container as the default safe local target.

---

## Quick Start

```bash
git clone https://github.com/Ayaan1911/Argus-Sentinel
cd Argus-Sentinel
cp .env.example .env      # set API_KEY to your own long random value
docker compose up --build -d
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| OWASP Juice Shop (bundled scan target) | http://localhost:3000 |

Every API call other than `/health` requires the `X-API-Key` header, matching the `API_KEY` set in `.env`. Run a scan against the bundled Juice Shop instance to verify the full pipeline:

```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "X-API-Key: <your API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"target": "juice-shop"}'
```

`db` and `redis` are not exposed to the host — only `api` (8000), `frontend` (5173), and the `juice-shop` target container (3000) publish ports.

---

## The Pipeline

Scanning is a real sequential pipeline, not four independent tool calls fired in parallel:

```
subfinder(target)
  → httpx(target + all discovered subdomains)
    → nmap(target + only the discovered subdomains httpx confirmed live)
    → nuclei(target + only the discovered subdomains httpx confirmed live)
```

subfinder's output feeds httpx so every discovered subdomain gets a liveness check; nmap and nuclei then only spend time on the target plus whatever subfinder found that httpx actually confirmed responds — not the full unfiltered subdomain list. Candidates with no DNS record at all (neither A nor CNAME) are discarded before they ever become a finding, since third-party passive sources occasionally fabricate results for domains they have no real data on. Each stage's outcome is tracked independently in `stage_status` (`success` / `failed` / `timeout` / `no_binary` per tool), not collapsed into one overall scan status.

---

## Scoring: Correlation, Reasoning, and Confidence

Raw scanner output alone isn't a finding — it's an input. Three engines turn it into something explainable:

- **Reasoning Engine** — assigns a deterministic base risk score per finding type (port/service, vulnerability, technology, subdomain), then applies labeled modifiers (internet-facing, no authentication, outdated version, admin panel exposed, WAF detected, etc.) sourced from the scanner's raw output and the matching intelligence library entry. Every score ships with a `reasoning_breakdown` array showing exactly which modifiers fired and why.
- **Correlation Engine** — looks across all of a scan's findings together, not just one at a time (e.g. an exposed database *and* no authentication together is worse than either alone), and applies scan-wide modifiers on top of each finding's own reasoning score.
- **Confidence Engine** — separately scores how *certain* a finding is (scanner reliability + corroborating evidence + intelligence-library match), independent of how severe it is — a finding can be high-confidence and low-severity, or the reverse.

All three are backed by **`argus-intelligence/`**, a 57-entry JSON knowledge base (25 services, 18 technologies, 14 vulnerability classes) that the scoring engines look up by scanner-reported name/product — not a hardcoded lookup table inline in the scoring code.

---

## Security Posture

- **Authentication** — every endpoint except `/health` requires a valid `X-API-Key` header; requests without one get a `401`.
- **SSRF target validation** — submitted targets are resolved and rejected with a `422` before any scan is dispatched if they resolve to a loopback, link-local (including the `169.254.169.254` cloud metadata address), private, reserved, or multicast address. The bundled `juice-shop` container is explicitly allowlisted as the intended local target.
- **Rate limiting** — scan creation (`POST /api/v1/scans/`) is limited to 5 requests/minute per client.
- **CORS** — restricted to the origins listed in `ALLOWED_ORIGINS` (`.env`), not wide open.

---

## Frontend

React 18 + Vite + Tailwind, talking to the API over axios with the API key wired in automatically:

| Page | Route | Purpose |
|---|---|---|
| Dashboard | `/` | Scan history, severity distribution, finding-type breakdown |
| New Scan | `/scan/new` | Submit a target + choose an audience persona |
| Scan Detail | `/scan/:scan_id` | Live per-tool `stage_status`, findings list, combined risk level — polls the scan while running and stops once it reaches a terminal status |
| Finding Detail | `/scan/:scan_id/finding/:finding_id` | Full reasoning breakdown, attack patterns, recommended actions, audience-specific guidance for one finding |
| Intelligence Library | `/intelligence` | Browse the 57-entry services/technologies/vulnerabilities knowledge base directly |

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Python 3.11 |
| Task queue | Celery + Redis |
| Database | PostgreSQL 15 (SQLAlchemy ORM, no raw SQL) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Scanners | subfinder, ProjectDiscovery httpx, nmap, nuclei |
| Containers | Docker Compose |

---

## Real Scan Output

From an actual scan run against the bundled Juice Shop target (`target: "juice-shop"`) — not a fixture:

```json
{
  "status": "completed",
  "stage_status": {
    "subfinder": { "status": "success" },
    "httpx":     { "status": "success" },
    "nmap":      { "status": "success" },
    "nuclei":    { "status": "success" }
  },
  "finding_count": 4
}
```

| Type | Severity | Risk Score | Title |
|---|---|---|---|
| technology | low | 3.0 | Live Host: http://juice-shop:3000 |
| port | informational | 2.0 | Port 3000/tcp: ppp |
| vulnerability | informational | 1.0 | Public Swagger API - Detect: http://juice-shop:3000/api-docs/swagger.yaml |
| vulnerability | informational | 1.0 | Prometheus Metrics - Detect: http://juice-shop:3000/metrics |

subfinder correctly reports 0 real subdomains for `juice-shop` (it isn't a real internet domain — any passive-source hits get resolved and discarded if they don't actually exist in DNS). Risk scores vary by finding type and the specific data each scanner returned — not a flat default.

---

## Testing

```bash
cd backend && pytest        # 48 tests
cd frontend && npm test     # vitest
```

The backend suite includes pure-Python unit tests for the scoring engines and scanner argv/output-parsing logic, plus a real Postgres-backed integration suite (`test_routes.py`, `test_scan_tasks.py`) that spins up a throwaway Postgres container via Docker and exercises actual API routes and task orchestration end-to-end — those tests skip automatically if Docker isn't reachable (e.g. running the suite from inside a container itself with no Docker-in-Docker access) rather than silently passing on mocked data. The frontend suite covers `ScanDetail`'s polling logic (`nextPollDelay`) directly.

---

## Known Limitations

- **Intelligence library coverage**: 57 entries across services/technologies/vulnerabilities. A finding whose scanner-reported name/product doesn't match an entry still gets a base reasoning score, just without library-sourced guidance.
- **nmap's outdated-version detection** only covers products it has a matching intelligence-library entry for (openssh, apache, nginx, mysql, postgresql, redis, mongodb) — an unlisted stack won't trigger "outdated version" modifiers even if nmap fingerprints it correctly.
- **httpx/nuclei port coverage**: beyond 80/443, only a fixed list of common alternate web ports (3000, 8000, 8080, 8888) is probed — a target on an uncommon port outside that list won't be found.
- **External target scanning** requires the `worker` container to have outbound internet access; passive sources like subfinder's will reach out to third-party APIs over the network for any target, including ones you don't expect to need it.

---

The original product vision and design philosophy this project started from is in [ARGUS_SENTINEL.md](ARGUS_SENTINEL.md) — note that document predates the current implementation and describes a broader long-term scope than what exists today; this README is the accurate description of the current codebase.

---

## License

MIT.
