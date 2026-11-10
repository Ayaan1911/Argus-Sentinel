# Argus Sentinel hardening audit — 2026-11-11

Reviewed at `31af522` on `codex/step-4-hardening-audit`. This is a review, not an implementation. Assumed load: one self-hosted worker handling repeated scans, plus the documented optional public demo. Findings are ordered by risk; approval is required before changing application behavior.

## Must fix

1. **The Windows checkout cannot start the API container.** `backend/start.sh:1-4`, `backend/Dockerfile:36-40`, `docker-compose.yml:35-36`.
   - **Case:** On the fresh Windows clone, Git reported `i/lf w/crlf` for `backend/start.sh`; the API container exited with `exec ./start.sh: no such file or directory`. The bind mount presents the CRLF working copy to Linux, so the script's shebang names `/bin/sh\r`.
   - **Small fix:** Add a `.gitattributes` rule that checks `*.sh` out with LF, then verify a fresh Windows clone and Compose rebuild. This should be fixed before interpreting any later API result.

2. **A fresh PostgreSQL database cannot complete migrations.** `backend/alembic/versions/5da69c924778_initial_tables.py:19-27`, `backend/alembic/versions/9429a108190d_add_scan_stage_status.py:20-24`, `backend/start.sh:3-4`.
   - **Case:** The initial revision creates no tables; `alembic upgrade head` failed on the fresh volume with `relation "scans" does not exist` when the next revision tried to alter it. `start.sh` lacks `set -e`, so after its line endings are fixed it may continue to launch Uvicorn despite the migration failure.
   - **Small fix:** Make the initial migration create the original tables, stop startup on migration error, and run migrations against an empty PostgreSQL database in CI. Check how any existing deployed volumes were initialized before changing migration history.

3. **Scanner requests can leave the validated target scope.** `backend/app/schemas/scan.py:26-70`, `backend/app/tasks/scan_tasks.py:75-94`, `backend/app/scanners/httpx.py:82-88`.
   - **Case:** Validation checks the submitted hostname once. Discovered names pass to httpx, Nmap, and Nuclei without a scope or private-IP check; httpx follows redirects. A poisoned discovery result or a public endpoint redirecting to an internal address can direct the worker at a target the caller could not submit directly. The validator also acknowledges a DNS rebinding window.
   - **Small fix:** Require discovered names to belong to the requested domain, validate every resolved destination at scanner dispatch, and reject or constrain redirects to out-of-scope/private addresses. Preserve the deliberate `juice-shop` exception.

4. **The public demo key grants deletion and access to all scan histories.** `frontend/src/api/client.js:3-9`, `backend/app/main.py:91-102`, `backend/app/routers/scans.py:176-192,337-347`.
   - **Case:** The browser sends a fixed key. In demo mode that key is intentionally public, yet the same key authorizes listing scans, reading findings, and deleting any scan ID. One visitor can erase another visitor's scan record; the UI need not expose the delete button for the API call to work.
   - **Small fix:** Give public demo traffic only the read/create operations it needs, with deletion behind a separate non-public credential. Keep normal self-hosted instances private until per-user access control exists.

5. **Failed or undispatched scans can be shown as successful or remain pending.** `backend/app/tasks/scan_tasks.py:114-117,171-181`, `backend/app/routers/scans.py:157-167`, `frontend/src/pages/ScanDetail.jsx:289-299`.
   - **Case:** A scanner timeout or missing binary is recorded in `stage_status`, but the worker still writes `completed`; with zero findings the UI says “Target Appears Secure.” If Redis rejects `run_scan.delay()` after the row commits, that row stays pending and the next request reuses it.
   - **Small fix:** Record an incomplete/failed state when required stages fail, and mark or remove a row when dispatch fails. Make the UI distinguish an incomplete scan from a completed scan with no findings.

## Should fix

6. **Port findings from different hosts share one identity.** `backend/app/scanners/nmap.py:90-137`, `backend/app/engines/diff.py:17-24,40-67`, `backend/app/engines/correlation.py:167-180`.
   - **Case:** Nmap reads each host address but omits it from finding data and builds titles like `Port 22/tcp: ssh`. Two scanned hosts with SSH port 22 create the same `(type, title)` diff key, and correlation matches both by title. One host's score change can be attributed to the other.
   - **Small fix:** Persist the host/address on every port finding and use a stable host+port+protocol identity for diff and correlation. Add a two-host regression test.

7. **Correlation changes the score without updating severity.** `backend/app/tasks/scan_tasks.py:163-171`, `backend/app/engines/correlation.py:178-180`, `backend/app/routers/findings.py:32-37`.
   - **Case:** A finding can cross from medium to high or critical after a correlation modifier, but the stored `severity` still reflects its base score. The numeric score, badge, severity filter, and dashboard counts then disagree.
   - **Small fix:** Derive and persist severity from the final score after applying modifiers; retain base severity separately only if the UI needs it. Add a threshold-crossing test.

8. **The UI drops findings after the first 50 while list endpoints load everything.** `backend/app/routers/findings.py:20-43`, `frontend/src/pages/ScanDetail.jsx:66-71`, `backend/app/routers/scans.py:59-64,176-190`.
   - **Case:** A scan with 80 findings returns 80 in its summary but the detail page requests only the default first 50 and offers no next page. Meanwhile dashboard statistics and scan listing materialize every finding or every scan with all related findings, so response cost grows with history.
   - **Small fix:** Page through findings in the UI, paginate scan history, and calculate dashboard counts with grouped SQL queries. Verify the UI can display finding 51 and that totals remain consistent.

## Decision point

The first two issues block a trustworthy fresh-stack scan; issues 3-5 affect scope, permissions, and result truthfulness. Fix those before using the public demo or treating a “secure” result as evidence. No fixes were made in this step. The prior 125-test/21-test CI success does not exercise a fresh Compose startup or a live Juice Shop diff.
