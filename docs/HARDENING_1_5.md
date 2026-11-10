# Hardening findings 1–5

Implemented on `codex/hardening-1-5` after the audit in `HARDENING_AUDIT.md`.

1. Linux startup scripts are checked out with LF on Windows. The API entrypoint stops if migrations fail.
2. The initial Alembic revision creates scans and findings; later revisions add their columns. The DB-backed test fixture now migrates a fresh PostgreSQL database rather than creating tables from the current ORM.
3. The worker checks the root and each discovered hostname before handing it to a scanner. Discovered hosts must be within the root domain and resolve only to public addresses; `juice-shop` remains the single local exception. The demo `scanme.nmap.org` target gets a DNS check at the worker. HTTPX and Nuclei redirects are disabled, and out-of-scope scanner results are discarded.
4. In demo mode, reads and reuse are limited to rows marked `is_demo`; deletes return 403. Demo scans remain shared with other demo visitors because the public demo has no visitor identity. Do not put private targets or sensitive findings into demo records.
5. Any failed scanner stage leaves the overall scan `failed` while retaining partial findings. A queue dispatch error marks the new row `failed` and returns 503, so a later request can retry. The detail page labels partial results.

## Verification

- Backend: 131 tests passed, including empty-DB migration, demo isolation, dispatch failure, DNS scope, and redirect arguments.
- Frontend: 21 tests passed; production build succeeded.
- Local Compose: all six services started after a full rebuild; the previously empty local PostgreSQL volume migrated to `c7f0a3d9e21b`, with scans and findings present. The two saved scans and API diff survived a second full rebuild. Docker build inputs now exclude generated Python and Node dependencies.
- Live Juice Shop scans: first `3c80cb9c-b6ec-4c14-bdeb-33e152dbf413` completed with 14 findings; second forced scan `45db20a4-2c46-44f2-aef6-c7b662e23aee` completed with 11. All four scanner stages reported success in both scans.
- Live API diff of second against first: 1 new, 4 resolved, 0 changed, 10 unchanged. These categories describe observed scanner output, not a verified change in the target security posture.

## Operational limits

- DNS is rechecked at scanner handoff, but a hostname can rebind between that check and the scanner's own DNS lookup. Public deployments still need network egress rules that block private, loopback, link-local, and metadata destinations, with a narrow exception for the bundled Juice Shop container.
- Existing installations with manually created tables and no Alembic version marker require a schema inspection and backup before upgrading. The migration path was verified against an empty database, not an unknown existing production schema.
- The frontend install reported 14 dependency advisories (7 moderate, 7 high). They have not been triaged in this step.
- Findings 6–8 in the audit remain open for the next approved step.
