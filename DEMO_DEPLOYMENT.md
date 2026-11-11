# Public demo preparation (not a deployment record)

The optional demo overlay is `docker-compose.demo.yml`. It sets demo mode on the API and frontend. The backend validator currently accepts **two** exact targets in demo mode: the bundled `juice-shop` container and `scanme.nmap.org`. This guide is for preparing and checking a future self-hosted demo; no Azure VM or public service is configured by this repository.

## Current limits before public exposure

- The base Compose file publishes the API on `8000`, the Vite frontend on `5173`, and Juice Shop on `3000` to all host interfaces. Its frontend runs Vite's development server and the API runs Uvicorn with `--reload`. Do not treat that stack as a production server configuration.
- The worker rechecks DNS and scope before scanner handoffs, but a hostname can rebind before the scanner connects. A public host needs outbound network controls that block private, loopback, link-local, and cloud metadata destinations while allowing the intended Juice Shop container. Target validation alone does not close this gap.
- Demo visitors share a public API key and can read each other's demo scans. Deletion is disabled, ordinary scan records are hidden, and demo records become eligible for hourly pruning after 24 hours. Do not store sensitive findings in demo scans.
- The 3/minute demo scan-creation limit uses the address the API sees. Behind Caddy and Docker's port publishing, that may be a shared proxy address. Verify trusted client-address handling before claiming a per-visitor limit. The separate Redis daily ceiling is global and uses a UTC calendar-day key, not a rolling 24-hour window.

Resolve the public-host exposure, egress, proxy-address, and production-serving points before publishing a demo. The commands below are a configuration rehearsal, not evidence that those points are solved.

## Configure a rehearsal

1. Copy `.env.example` to `.env` and `frontend/.env.example` to `frontend/.env`. Keep both files out of git. In the root `.env`, set `DEMO_MODE=true`, a generated `SECRET_KEY` and `API_KEY`, `DEMO_API_KEY` to the chosen public demo key, `ALLOWED_ORIGINS` to the eventual HTTPS origin, an affordable `DEMO_SCAN_DAILY_LIMIT`, and `VITE_API_URL=https://demo.example.com/api/v1` after replacing the domain. The worker reads the root `.env` through Compose, so **`DEMO_MODE=true` there is required**; the overlay sets it only for the API. Compose also interpolates `VITE_API_URL` from the root `.env` for the frontend overlay. The public demo key is not a secret or a user identity.
2. In `frontend/.env`, set `VITE_DEMO_MODE=true`, `VITE_API_KEY` to the same public demo key, and `VITE_API_URL` to the same HTTPS URL. The overlay injects these Vite settings into the frontend container and its values take precedence over the frontend env file. Keep both files consistent so a different Compose command does not produce an unexpected configuration. `VITE_API_URL` must be the browser-reachable HTTPS address, not `localhost` on a visitor's computer.
3. Review the rendered configuration without printing or sharing its secret values: `docker compose -f docker-compose.yml -f docker-compose.demo.yml config --quiet`. For a local-only check, the usual command is `docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build -d`. This still starts the development stack; keep it on a trusted machine.

The demo validator in `backend/app/schemas/scan.py` locks API scan creation to `juice-shop` and `scanme.nmap.org`. `backend/app/tasks/scan_tasks.py` applies scope checks to discovered names and rechecks public DNS destinations at scanner handoff. Normal self-hosted mode accepts other authorized public targets after validation and treats Juice Shop as its one internal exception.

## Reverse proxy example for a future host

[`Caddyfile.example`](Caddyfile.example) routes `/api/*` and `/health` to the API and other paths to the frontend, preserving the API path. It assumes Caddy runs on the **same host** as Compose. Replace `demo.example.com` with a domain pointed at that host. Caddy can manage HTTPS for a qualifying domain when ports 80 and 443 are reachable; see the [Caddy HTTPS documentation](https://caddyserver.com/docs/automatic-https) and [handle directive](https://caddyserver.com/docs/caddyfile/directives/handle).

Before starting a public reverse proxy, bind the API and frontend port mappings to the host loopback interface (`127.0.0.1:8000:8000` and `127.0.0.1:5173:5173`), and remove the Juice Shop host port mapping entirely. The worker reaches Juice Shop by its internal Compose service name. Keep PostgreSQL and Redis unpublished. Allow inbound web traffic only on 80/443 and restrict administrative access separately. Container port publishing and firewall behavior must be verified on the actual host. A Caddy process in a separate container cannot use `127.0.0.1` to reach these Compose services without a different network configuration.

## Checks after the public-host prerequisites are implemented

- Confirm the rendered Compose configuration has demo mode on **both API and worker**, the frontend points at the HTTPS API URL, and the three app/test-target ports cannot be reached from outside the host.
- Confirm `GET https://demo.example.com/health` works; an unauthenticated API scan request gets `401`; a scan request for `example.com` with the public demo key gets `422`; a request for `juice-shop` is accepted and eventually reaches a terminal status. A newly accepted scan may be returned as `pending` initially.
- Confirm the frontend shows the demo target controls, that a demo visitor cannot delete a scan, and that ordinary scan records do not appear in demo reads. Check the browser console for mixed-content or CORS errors.
- Confirm worker egress filtering blocks a re-resolved private/metadata destination, the public key is understood to grant shared demo access, and rate-limit behavior is correct through the actual proxy path. Do not rely on a browser-only check for these properties.

The current repository does not implement all public-host prerequisites. See `docs/HARDENING_1_5.md` for verified behavior and remaining risks, and `docs/HARDENING_AUDIT.md` for open findings 6–8.
