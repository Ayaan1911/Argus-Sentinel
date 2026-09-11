# Deploying the Public Demo

This deploys the locked-down demo variant described in `docker-compose.demo.yml` — scans are restricted to the bundled `juice-shop` target only, by construction (see `backend/app/schemas/scan.py`'s `DEMO_MODE` branch), not by a policy someone could forget to enforce.

## Where to run it

The existing setup is plain Docker Compose with 6 services (db, redis, juice-shop, api, worker, frontend) sharing a Docker network. **A small VPS running Docker Compose is the simplest option** — it runs the exact same `docker compose` commands you already use locally, no translation needed. Railway and Fly.io are container-first platforms that don't run a multi-service `docker-compose.yml` as-is; they'd need each service split into a separate app/service with a shared managed Postgres/Redis, which is real extra work for a "try it live" demo. If you already have a Railway/Fly.io account and want to go that route anyway, the environment variables below are what you need regardless of platform — but a VPS is the path that requires zero adaptation of the existing files.

Any small VPS (a $5–6/mo droplet on DigitalOcean, Hetzner, Linode, etc. — 2GB RAM minimum, nuclei template downloads and concurrent scan tooling want the headroom) with Docker and the Compose plugin installed works.

## Steps

1. **Provision a VPS**, SSH in, install Docker + the Compose plugin (`curl -fsSL https://get.docker.com | sh` covers Docker itself on most distros; the Compose plugin ships with recent Docker installs — confirm with `docker compose version`).

2. **Clone the repo:**
   ```bash
   git clone https://github.com/Ayaan1911/Argus-Sentinel
   cd Argus-Sentinel
   ```

3. **Set up `.env`** (backend) from `.env.example` — for a demo deployment, the values that matter:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   - `SECRET_KEY` — generate a real random value (`openssl rand -hex 32`), same as any deployment.
   - `API_KEY` — generate a real random value too. It's never used while `DEMO_MODE=true` (demo visitors authenticate with `DEMO_API_KEY` instead), but leaving the placeholder default around costs nothing to avoid.
   - `ALLOWED_ORIGINS` — set to your actual public domain (e.g. `https://demo.your-domain.com`), not `localhost`.
   - `DEMO_API_KEY` — the fixed key demo visitors will use. This one's meant to be public — put it directly in your frontend's public docs/README, since the whole point is zero setup for visitors.
   - `DEMO_SCAN_DAILY_LIMIT` — defaults to 500/day; lower it if you're worried about compute cost, raise it if 500 is too tight for your traffic.

4. **Set up `frontend/.env`** from `frontend/.env.example`:
   ```bash
   cp frontend/.env.example frontend/.env
   ```
   Edit `frontend/.env`:
   - `VITE_API_URL` — your public API URL (e.g. `https://demo.your-domain.com/api/v1` or `http://your-vps-ip:8000/api/v1`).
   - `VITE_API_KEY` — **must equal the same `DEMO_API_KEY` value** you set in step 3.
   - `VITE_DEMO_MODE` — set to `true`.

   (`docker-compose.demo.yml` also injects `DEMO_MODE`/`DEMO_API_KEY`/`VITE_DEMO_MODE`/`VITE_API_KEY` as container environment variables layered on top of these files — set them in `.env`/`frontend/.env` too so a plain `docker compose up` without the demo overlay doesn't accidentally serve real-looking but broken config. Keeping both in sync is simplest.)

5. **Bring it up with the demo overlay:**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build -d
   ```

6. **Put a reverse proxy in front of it** (Caddy or nginx) for TLS — this project's Compose setup doesn't include one, and a public demo should be on HTTPS. A minimal Caddy config:
   ```
   demo.your-domain.com {
       reverse_proxy /api/* localhost:8000
       reverse_proxy localhost:5173
   }
   ```

7. **Verify**, from your own machine (not the VPS):
   ```bash
   curl -X POST https://demo.your-domain.com/api/v1/scans/ \
     -H "X-API-Key: <your DEMO_API_KEY>" -H "Content-Type: application/json" \
     -d '{"target": "example.com"}'
   # expect a 422 — anything but juice-shop is rejected

   curl -X POST https://demo.your-domain.com/api/v1/scans/ \
     -H "X-API-Key: <your DEMO_API_KEY>" -H "Content-Type: application/json" \
     -d '{"target": "juice-shop"}'
   # expect a 200 with a scan id
   ```
   And open the frontend URL in a browser — you should see the demo banner and the locked target field on the New Scan page.

## What's actually protecting this

- `DEMO_MODE=true` makes `validate_scan_target()` in `backend/app/schemas/scan.py` reject every target except `juice-shop` — including ones that would normally pass (this isn't the SSRF check getting stricter, it's a total inversion: juice-shop goes from "the one exception" to "the only valid value").
- Scan creation is rate-limited to 3/minute per IP in demo mode (vs. 5/minute normally), keyed by remote address specifically because every visitor shares the same public `DEMO_API_KEY` — keying by API key (the normal behavior) would put all demo traffic in one shared bucket.
- A rolling daily ceiling (`DEMO_SCAN_DAILY_LIMIT`, default 500) tracked in Redis caps total scan creation regardless of per-IP limits, so many distinct visitors each staying under their own limit still can't runaway the compute cost.
- Auth still runs — `DEMO_API_KEY` replaces `API_KEY` as the value visitors need, it isn't a bypass.

None of this touches `docker-compose.yml` itself or changes behavior when `DEMO_MODE` is unset/false — a normal self-hosted deployment is completely unaffected.
