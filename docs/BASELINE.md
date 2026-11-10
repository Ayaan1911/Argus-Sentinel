# Baseline — 2026-11-11

Branch: `codex/step-2-baseline` (starting from `b40e64b`). This was a fresh clone and a fresh Docker Compose database volume. No application source was changed during this baseline.

## Commands and observed results

| Check | Command | Result |
| --- | --- | --- |
| Local environment | `bash scripts/setup.sh` | Created ignored `.env` and `frontend/.env` with matching generated API keys. Keys are not recorded here. |
| Clean stack build | `docker compose up --build -d` | Images built and six containers were created, but API and worker exited. PostgreSQL, Redis, Juice Shop, and frontend remained running. |
| Frontend availability | HTTP GET `http://localhost:5173` | 200. |
| API availability | HTTP GET `http://localhost:8000/health` | Connection refused. |
| Frontend tests | `docker compose exec -T frontend npm test -- --reporter=default` | 21 passed in 4 files. |
| Backend tests in API image | `docker compose run --rm --no-deps api pytest -q` | 70 passed, 3 failed, 52 skipped. The failures came from missing `psycopg`; Docker-backed tests skipped because the container could not access Docker. |
| Backend tests on Windows, declared dependencies only | `venv/Scripts/python.exe -m pytest -q` from `backend/` | 70 passed, 3 failed, 52 errors. All failures/errors were blocked by missing `psycopg`. |
| Backend tests after adding test-only packages locally | `venv/Scripts/python.exe -m pytest -q --tb=line` from `backend/` | 125 passed, 8 warnings. Installed `psycopg[binary]` and `httpx2` only into ignored `backend/venv`; neither dependency file nor source code was changed. |
| Fresh migration | `docker compose run --rm --no-deps api alembic upgrade head` | Failed: `relation "scans" does not exist` when the second migration tried to add `stage_status`. |

## Blockers to the requested two real scans

1. The API exits with `exec ./start.sh: no such file or directory`. `git ls-files --eol backend/start.sh` shows LF in Git but CRLF in the Windows working tree, so the Linux shebang cannot run through the bind mount.
2. The worker exits with `ModuleNotFoundError: No module named 'psycopg'`. Current unpinned SQLAlchemy selects the `psycopg` driver for the sync URL, but `requirements.txt` installs only `psycopg2-binary`.
3. On a fresh database, Alembic's initial revision creates no tables, so the following revision fails while altering `scans`.

The API never became available. No scan was submitted, so two Juice Shop scans and the live diff view could not be verified. The frontend was reachable, but that does not establish that the full product works.

## Documentation mismatch

The README states 123 backend tests; the full Windows run collected and passed 125 after the two local test-only packages were installed. Its 21 frontend tests are accurate for this checkout. `CLAUDE.md` still says no frontend test runner exists; Vitest is configured and ran successfully.

## Next step

These startup and dependency blockers need focused fixes before a real scan baseline or working CI can be demonstrated. Do not treat the 125 passing tests as evidence that a fresh Compose deployment starts successfully.

