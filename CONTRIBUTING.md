# Contributing to Argus Sentinel

Thanks for considering a contribution. This covers the project as a whole; if you specifically want to add a new entry to the intelligence library (services/technologies/vulnerabilities JSON), skip ahead to [Intelligence Library Contributions](#intelligence-library-contributions) below — that's a self-contained, no-Python/React-required path with its own guide.

## Getting a Local Dev Environment Running

```bash
git clone https://github.com/Ayaan1911/Argus-Sentinel
cd Argus-Sentinel
bash scripts/setup.sh
docker compose up --build -d
```

That's it — `scripts/setup.sh` creates `.env` and `frontend/.env` from their `.example` templates with a real, matching, randomly-generated `API_KEY` already filled in on both sides, so there's nothing left to manually edit for local dev. It won't touch either file if it already exists (safe to re-run). Requires Docker and the Compose plugin (`docker compose version` to confirm you have both) — that's the one real prerequisite this doesn't install for you.

Once it's up:

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API docs | http://localhost:8000/docs |
| OWASP Juice Shop (bundled scan target) | http://localhost:3000 |

Verify the full pipeline works with a real scan:

```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "X-API-Key: $(grep '^API_KEY=' .env | cut -d= -f2-)" \
  -H "Content-Type: application/json" \
  -d '{"target": "juice-shop"}'
```

If you want to iterate on the backend outside Docker (faster reload than rebuilding the container), or need any other command — `docker compose down`, running the frontend dev server standalone, etc. — see the Commands section in [CLAUDE.md](CLAUDE.md#5-commands), which is kept as the single source of truth for these so they don't drift out of sync across multiple docs files.

## Running Tests

```bash
cd backend && pytest        # 119 tests
cd frontend && npm test     # vitest, 12 tests
```

The backend suite includes pure-Python unit tests (scoring engines, scanner argv/output-parsing, the intelligence-library schema validator) that need nothing beyond `pip install -r requirements.txt`, plus a real Postgres-backed integration suite (`test_routes.py`, `test_scan_tasks.py`) that spins up a throwaway Postgres container via Docker itself — so **Docker needs to be running and reachable** for the full suite to pass, not just for `docker compose up`. Those specific tests skip automatically (rather than failing) if Docker isn't reachable — for example, if you run `pytest` from inside the `api` container itself, which has no Docker-in-Docker access. Run it on your host, with Docker running, to get the full suite rather than a partial one.

## Intelligence Library Contributions

Adding a new service/technology/vulnerability entry to `argus-intelligence/` is the best first contribution if you don't want to touch Python or React — vulnerability entries in particular are matched by data inside the JSON file itself (`nuclei_tags`/`title_keywords`), not by any code change.

Full guide, field reference, and a worked example: [argus-intelligence/CONTRIBUTING.md](argus-intelligence/CONTRIBUTING.md) (field-by-field schema: [argus-intelligence/SCHEMA.md](argus-intelligence/SCHEMA.md)).

Before opening a PR that touches `argus-intelligence/`, always run:

```bash
python scripts/validate_intelligence.py
```

This is also wired into the backend test suite (`test_intelligence_schema.py`) — a malformed entry fails `pytest` too, not just this standalone check — but running it directly gives you a faster feedback loop while you're actually editing a JSON file, since it doesn't need Docker/Postgres.

## Code Conventions

The conventions actually enforced in this codebase — subprocess calls always use `create_subprocess_exec()` with an argv list, never a shell string; every target string passes through `normalize_target()`; scanner error handling distinguishes binary-not-found/timeout/non-zero-exit/malformed-output rather than one generic catch-all — are documented in [CLAUDE.md's Conventions section](CLAUDE.md#4-conventions), which is the single source of truth for them. Read that before touching any scanner wrapper code so you're not restating (or accidentally contradicting) it here.

## Pull Request Expectations

- **Tests included.** A behavior change without a test covering it will get asked for one. See "Running Tests" above for how to actually run the suite before you open the PR, not after.
- **A clear PR description**, written the way this project's own `notes.md` session entries are (see [CLAUDE.md's Session Memory Protocol](CLAUDE.md#8-session-memory-protocol-notesmd) for the format, if you want a concrete example of the level of detail expected) — what changed, why, and anything you noticed but deliberately didn't fix. "Fixed a bug" with no further explanation isn't enough to review confidently.
- **Don't touch unrelated files.** If you notice something unrelated that seems wrong while you're in there, mention it in the PR description or open a separate issue — don't fold an unrelated fix into the same diff. Reviewing "add feature X" is a lot harder when it's tangled with "also reformatted file Y."
- **Small, focused PRs** over one PR doing several unrelated things. A new intelligence-library entry and a scanner bugfix are two PRs, not one.

## Project Scope

Argus Sentinel is a tool for **external-target web reconnaissance and risk-scoring** — subfinder/httpx/nmap/nuclei against a domain or IP you're authorized to test, turned into risk-scored, explained findings. That's the whole shape of the project, and it draws some boundaries worth knowing before you propose a feature:

**In scope**: anything that makes the recon pipeline more accurate, the scoring more correct, the intelligence library more complete, or the findings more explainable/actionable for the audience personas this project already serves (student, developer, bug bounty hunter, pentester, security team).

**Explicitly out of scope right now** (see [CLAUDE.md's Project Overview](CLAUDE.md#1-project-overview) for the canonical list): screenshots/gowitness, JS file extraction, secret detection, endpoint mining, subdomain takeover *verification* (as opposed to the takeover *candidate flagging* subfinder already does), AI/LLM-based summarization, PDF export. These were part of an earlier, different project direction and won't be accepted without an explicit decision to bring them back in — don't assume a PR adding one of these will be merged just because it's well-built.

**Out of scope by design, not just by current priority**: this is a tool for reconnaissance against *infrastructure* (domains, IPs, exposed services) that you're authorized to test — not a tool for gathering information about *people* (OSINT-on-individuals, social engineering / phishing-content generation, deception or impersonation tooling of any kind). If a proposed feature's target is a person rather than a system, it doesn't fit this project regardless of how well it's implemented.

When genuinely unsure whether something fits, open an issue describing the idea before investing time in a PR.
