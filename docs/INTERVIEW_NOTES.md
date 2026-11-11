# Argus Sentinel interview notes

Use these notes to explain the code that exists today. The [architecture diagram](../README.md#architecture) shows the service and data flow; [measured metrics](METRICS.md) records how the numbers below were obtained.

## Thirty-second explanation

Argus Sentinel is a self-hosted reconnaissance tool for targets you are authorized to test. A React frontend sends a target to FastAPI. The API validates it, saves a pending scan in PostgreSQL, and puts a job on Redis. A Celery worker runs Subfinder, httpx, Nmap, and Nuclei in order. It converts their output into findings, calculates explainable risk and confidence scores from a JSON intelligence library, applies correlation rules, and saves the results. The frontend displays the scan, its per-tool outcome, and changes from an earlier completed scan. This is deterministic scoring, not a language model.

## Why the pipeline is sequential

1. Subfinder proposes names beneath the submitted domain. The worker discards names outside that domain.
2. httpx probes the submitted root and discovered names that pass the scope check. Only discovered names that httpx confirms live proceed. The submitted root remains in scope even if httpx cannot confirm it.
3. Nmap checks the root and those live discovered hosts for ports and services. Nuclei checks the same hosts, using a live URL with its observed port when httpx found one.
4. At each active handoff, the worker checks scope and resolves destinations again. The scanners disable redirects where applicable. A failed scanner stage makes the overall scan `failed`, while partial findings remain available.

This order avoids sending every unverified passive discovery to the active scanners. It also lets a scan be explained as a progression from candidate names to observed live services. The four tools are still independent processes; a reported finding is evidence to investigate, not proof that a target is exploitable. See `backend/app/tasks/scan_tasks.py` and `backend/app/scanners/`.

## How the scores work

- `FindingProcessor` matches scanner data to the 51 JSON intelligence entries where possible. The reasoning engine starts with a base score for the finding type and adds named, evidence-based modifiers. The stored `reasoning_breakdown` explains the arithmetic; risk scores are capped at 10.
- The confidence engine separately estimates how strong the evidence is from scanner source, corroborating fields, and an intelligence match. High confidence does not mean high severity.
- The correlation engine inspects the scan's findings together. Six named rules can amplify a finding when relevant signals occur together; `multiple_high_severity` affects the combined scan risk instead of an individual finding. A rule need not fire on every scan. The same finding data and library rules produce the same scores.
- Audience guidance changes the explanation and suggested actions, not the scanner evidence. There is no model call, generated exploit, or automatic vulnerability verification.

Current limitation: correlation can increase `final_risk_score` without updating the saved `severity` label. The numeric score and badge/filter can disagree. This is open audit finding 7, not an intentional scoring policy. See `backend/app/scanners/processor.py`, `backend/app/engines/`, and `docs/HARDENING_AUDIT.md`.

## How two scans are compared

Each scan creates new finding IDs, so the diff engine cannot match rows by UUID. It groups findings by lowercased type and exact title, pairs duplicates by position, then compares final risk score, severity, and confidence. Unpaired current findings are **new**; unpaired previous findings are **resolved**; paired findings are **changed** or **unchanged**. The API only compares completed scans of the same normalized target. `force_rescan=true` creates a fresh run when a recent completed result would otherwise be reused.

This is a practical heuristic. A renamed scanner title can appear as new plus resolved, and identical port titles on different hosts can be paired incorrectly. The latter is audit finding 6; a future stable identity should include host, port, and protocol. See `backend/app/engines/diff.py` and `backend/app/routers/scans.py`.

## Security decisions and their limits

- The API checks `X-API-Key` on scan and finding routes, uses constant-time comparison, and limits browser origins through `ALLOWED_ORIGINS`. The key is shared; there are no user accounts or per-user scan permissions.
- Normal target validation normalizes names, resolves addresses, and rejects private, loopback, link-local, reserved, multicast, and unspecified destinations. The bundled `juice-shop` hostname is a deliberate internal exception. The worker checks root and discovered names before active scanning and rejects out-of-scope results. DNS can still change after a check and before a scanner connects, so a public host needs outbound network restrictions as well.
- Scan creation is rate-limited to 5/minute normally and 3/minute in demo mode, with a Redis daily demo scan ceiling. The demo key is intentionally public, so it is not a personal identity or a secret. Behind a proxy, the IP-based limit needs trusted client-address handling; do not assume the current configuration gives each visitor a separate bucket.
- Demo mode permits only `juice-shop` and `scanme.nmap.org`, hides ordinary scan records, blocks deletion, and prunes demo records after about 24 hours. All demo visitors can still read each other's demo scans. Keep private targets and sensitive findings out of the demo.

## What I would improve next

1. Carry a stable host-aware finding identity through parsing, correlation, and diffing (audit finding 6).
2. Recompute stored severity from the final correlated score (finding 7).
3. Page through findings and scan history, and aggregate dashboard counts in SQL (finding 8).
4. Add network-level egress isolation and verified client-IP handling before a public demo. Triage frontend dependency advisories and test migrations against any existing production database before upgrading it.

## Evidence and honest scope

The measured local checkout had 131 backend tests, 21 frontend tests, 80% backend statement coverage, and a 132.79-second median across three completed local Juice Shop scans. These are measurements, not guarantees for other targets or hosts. A real Juice Shop run has shown all four stages and saved findings; some correlation rules were exercised in pipeline tests because that target does not naturally trigger them. The project does not include screenshot capture, JavaScript extraction, secret detection, endpoint mining, takeover verification, LLM summaries, or PDF export.
