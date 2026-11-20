# Public demo preparation

The optional [`docker-compose.demo.yml`](docker-compose.demo.yml) overlay serves one authorized target: the bundled Juice Shop container. It runs the scanner worker only on an internal Docker network with no external gateway. Normal self-hosted mode retains scanning of authorized public targets. The demo is prepared here; this repository does not deploy it to a public host.

## Configure

1. Use Docker Compose 2.24.4 or newer. Copy `.env.example` to `.env` and set `SECRET_KEY` and `API_KEY` to private random values, `DEMO_API_KEY` to the public demo key you want displayed in the browser, `ALLOWED_ORIGINS` to `https://YOUR_DOMAIN`, and `DEMO_DOMAIN` to that hostname without a scheme. Keep `.env` out of git. The demo overlay forces `DEMO_MODE=true` on both API and worker, sets production API serving, and builds the frontend with `/api/v1` as a same-origin API path.
2. Point `DEMO_DOMAIN` at the host and allow inbound TCP 80/443 for Caddy to obtain and renew HTTPS certificates. No other application port needs to be public. If another reverse proxy or CDN is in front, review its forwarded-address policy before relying on the per-visitor limit.
3. Check `docker compose -f docker-compose.yml -f docker-compose.demo.yml config --quiet`, then start with `docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build -d` on the intended host. This builds static frontend assets and runs the API without reload. Caddy is the only service with published ports. PostgreSQL, Redis, Juice Shop, API, and frontend are reachable only inside Compose.

The public demo key is shared, not an account identity. Visitors can read one another's demo scans; deletion is disabled, ordinary scans are hidden, and demo scans are pruned after about 24 hours. Do not place sensitive findings in the demo.

## Verify on the host

- Inspect `docker compose -f docker-compose.yml -f docker-compose.demo.yml ps` and the rendered configuration: only Caddy should publish host ports. The worker must be attached only to the `internal: true` private network; the API bridges the private and web networks.
- From the worker, confirm Juice Shop resolves and responds, and an outbound connection to `169.254.169.254` and a public IP fails. Test network isolation on the actual host; Docker configurations and host firewalls vary.
- Visit `https://YOUR_DOMAIN/health` and the dashboard. An unauthenticated scan request must return `401`, a demo-key request for `scanme.nmap.org` must return `422`, and a Juice Shop scan should finish with findings or an explicit scanner failure. The public API must not be directly reachable on port 8000.
- Send scan-creation requests through Caddy from two client addresses and verify separate 3/minute rate-limit buckets. Caddy replaces incoming `X-Forwarded-For`; Uvicorn trusts forwarded addresses only from Caddy's fixed `172.31.245.254` address. If this subnet conflicts with your host network, change both the Compose subnet/address and the Uvicorn `--forwarded-allow-ips` value together. A CDN in front requires a separate trust review.

The example [`Caddyfile.example`](Caddyfile.example) is for a manually hosted proxy with the normal development stack. The demo overlay uses [`Caddyfile.demo`](Caddyfile.demo) instead.

## Local rehearsal evidence

On 2026-11-17, a fresh isolated Compose project with Caddy bound to laptop loopback ports returned HTTPS `200` for the frontend and health endpoint, `401` for an unauthenticated API request, and `429` on the fourth scan request despite forged `X-Forwarded-For` values. The worker reached Juice Shop (`200`) and could not connect to `1.1.1.1` or `169.254.169.254`. Its Juice Shop scan completed in 102 seconds with three raw findings. These checks do not establish reachability, TLS issuance, or client-IP behavior on a future public host.
