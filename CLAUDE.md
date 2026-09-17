# CLAUDE.md

This file is read automatically by Claude Code at the start of every session in this repo. Follow it before doing anything else.

## Session Start Protocol

1. Read `notes.md` first, if it exists, before reading any source code. Treat it as ground truth for what happened in prior sessions — decisions made, what was changed and why, what's still open.
2. Only re-read source files for whatever the current task actually touches. Do not re-scan the whole codebase from scratch if notes.md already covers the relevant context.
3. If notes.md doesn't exist yet, this is effectively session one — proceed normally and create it at the end of this session per the protocol below.

## 1. Project Overview

Argus-Sentinel is an automated web reconnaissance and risk-scoring tool: a user submits a target domain, the backend runs subfinder, httpx, nmap, and nuclei against it, and a custom correlation/reasoning engine turns raw scanner output into risk-scored findings with audience-specific guidance (drawing on a 51-entry JSON intelligence library of known services, technologies, and vulnerabilities). It's built to be a genuinely usable local recon tool — for authorized testing of owned/permitted targets, with a bundled juice-shop container as the default safe local target — not a toy demo.

## 2. Tech Stack

- Backend: Python, FastAPI, Celery (task queue), Redis (broker), PostgreSQL (via SQLAlchemy ORM), pytest
- Frontend: React, Vite, Tailwind CSS — no test runner configured yet (vitest planned)
- Scanning tools invoked as subprocesses: subfinder, ProjectDiscovery httpx (not Python's httpx library — do not confuse the two), nmap, nuclei
- Deployment: Docker Compose (services: api, worker, frontend, db, redis, plus a bundled juice-shop target container)

## 3. Architecture

**Backend** — `backend/app/`:
- `routers/` — FastAPI route handlers: `scans.py`, `findings.py`, `intelligence.py`
- `scanners/` — one file per external tool: `subfinder.py`, `httpx.py`, `nmap.py`, `nuclei.py`, plus `processor.py` and `utils.py` for shared helpers
- `engines/` — the scoring system: `reasoning.py`, `correlation.py`, `confidence.py`
- `intelligence/` — loader reading `argus-intelligence/{services,technologies,vulnerabilities}/*.json` (51 files) into the scoring engine
- `models/`, `schemas/` — SQLAlchemy models and Pydantic schemas
- `tasks/` — Celery tasks, primarily `scan_tasks.py` which orchestrates the scan pipeline

**Frontend** — `frontend/src/`:
- `pages/` — `Dashboard`, `NewScan`, `ScanDetail` (the findings workspace), `FindingDetail`, `Intelligence` (a knowledge-base browser)
- `components/`, `api/` (contains `client.js`, the axios instance)

**Not part of this repo** (do not build without explicit instruction — see Current Focus below): screenshots/gowitness, JS file extraction, secret detection, endpoint mining, subdomain takeover verification tooling, AI/OpenRouter summarization, PDF export. These were part of an earlier, different project direction and are explicitly out of scope now.

## 4. Conventions

- Scanner subprocess calls always use `create_subprocess_exec()` with an argv list — never `create_subprocess_shell()` or string-interpolated commands. This is a hard rule, not a style preference, given the security surface of this tool.
- All external tool binary paths are absolute (matching Dockerfile install locations), not resolved from PATH — this avoids a prior bug class (PATH shadowing between ProjectDiscovery's httpx and Python's httpx CLI).
- All target strings pass through a shared `normalize_target()` helper (in `scanners/utils.py`) before being used by any scanner, so the same target is never treated as different literal values by different tools.
- All DB access goes through the SQLAlchemy ORM — no raw SQL string interpolation.
- Error handling in scanner wrappers should distinguish binary-not-found, timeout, non-zero exit, and malformed output as separate cases, not a single generic catch-all.
- Reuse the existing `argus-intelligence/` JSON data for vulnerability/technology lookups rather than hardcoding new lookup tables inline.

## 5. Commands

```bash
# Full stack (dev)
docker compose up --build -d
docker compose down

# Backend tests
cd backend && pytest

# Backend, running outside Docker for iteration
cd backend && uvicorn app.main:app --reload

# Frontend dev server
cd frontend && npm run dev

# Frontend build
cd frontend && npm run build
```

If any of the above drift from what's actually in `package.json` / `Makefile` / CI config, trust those files over this list and update this section.

## 6. Known Constraints / Gotchas — do not "fix" without asking

- The bundled juice-shop container is the intended default authorized local scan target. Do not remove it or restrict scans from reaching it as part of any SSRF-hardening work — it must remain explicitly allowlisted.
- `argus-intelligence/*.json` is treated as reference data, not application logic — don't refactor its structure without checking every consumer in `engines/` and `intelligence/loader.py`.
- If mid-remediation on a known audit finding (auth, SSRF validation, CORS, exposed DB/Redis ports, dead scoring branches, polling/pagination), check `notes.md` before assuming it's unfixed — it may be in progress or partially done in a way not yet reflected in a stale comment or TODO.
- Do not silently change scanner output field names/shapes without checking `engines/reasoning.py` and `correlation.py` — they key off specific field names in `raw_data`, and a rename there breaks scoring silently.
- **A running container does not necessarily reflect the latest code or schema.** This has twice caused a real change to look "missing" when it was actually present and committed: once because Vite's file watcher doesn't reliably trigger HMR over this project's Windows bind mount (an edited frontend file kept serving stale content from a container that was never restarted), and once because a pending Alembic migration was never applied to a long-running `api` container (migrations only run at container startup, via `start.sh`). Before any visual verification pass, and before reporting that a change didn't take effect, run `docker compose down && docker compose up --build -d` first — do not trust that an already-running container reflects what's currently on disk.

## 7. Current Focus

Actively being hardened, in this order: (1) authentication + SSRF target validation + CORS + exposed service ports + rate limiting + untracking `.env`, (2) turning the parallel independent scanner calls into a real sequential pipeline where subfinder's output feeds httpx/nmap/nuclei, and wiring the scanners to actually populate the fields the scoring engine already expects, (3) dead code and error-handling cleanup, (4) frontend env/timeout/pagination fixes, (5) test coverage for all of the above.

**Explicitly out of scope right now**: screenshots, JS extraction, secret detection, endpoint mining, takeover verification tooling, AI summarization, PDF export. Do not add these unless told to — the current goal is hardening and correctness of what exists, not scope expansion.

## 8. Session Memory Protocol (notes.md)

Maintain a file called `notes.md` at the project root as running memory across sessions. It is gitignored — treat it as local working memory, not project documentation (that's what this file is for).

**When to update it**: at the end of every session, before ending — even if the session was short or exploratory.

**What to capture**:
- Key decisions made this session and why
- Files changed, and a one-line reason for each
- Bugs found and/or fixed
- Open issues or half-finished work, stated plainly
- Any assumptions made that should be verified next time
- Next steps

**Format** — newest entry on top, dated, using this template per entry:

```markdown
## 2026-XX-XX — [short session title]

**Summary**: one or two sentences on what this session was about.

**Changes**:
- `path/to/file.py` — what changed, why

**Bugs found/fixed**:
- description → status

**Open items**:
- anything unresolved, stated plainly, not softened

**Assumptions to verify**:
- anything assumed but not confirmed

**Next steps**:
- what the next session should pick up
```

**Rules to keep it lean**:
- Do not restate the codebase structure or anything already covered in this CLAUDE.md — link back to the relevant section here instead of repeating it
- Do not duplicate detail that's already visible in git commit messages — summarize the "why," not the full diff
- When the file grows past roughly 10 entries, collapse the oldest entries into a single "Earlier sessions (summary)" block at the bottom, keeping only what's still relevant context, and delete the rest
- Newest entry always goes at the top, directly under the title, so the most recent session's context is the first thing read