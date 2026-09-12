#!/usr/bin/env bash
# One-time local dev setup: creates .env and frontend/.env from their
# .example templates (if not already present), with a real, matching random
# API_KEY already filled in on both sides — so `docker compose up --build -d`
# works immediately afterward with no manual .env editing required for a
# normal local dev loop.
#
# Usage: bash scripts/setup.sh
set -euo pipefail

cd "$(dirname "$0")/.."

gen_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 -c "import secrets; print(secrets.token_hex(32))"
  fi
}

if [ -f .env ]; then
  echo ".env already exists — leaving it untouched."
else
  cp .env.example .env
  api_key="$(gen_secret)"
  secret_key="$(gen_secret)"
  # -i.bak (not bare -i) works identically on both GNU sed (Linux) and
  # BSD/macOS sed, which otherwise disagree about -i's argument handling.
  sed -i.bak "s/^API_KEY=.*/API_KEY=${api_key}/" .env && rm -f .env.bak
  sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=${secret_key}/" .env && rm -f .env.bak
  echo "Created .env with a generated API_KEY and SECRET_KEY."
fi

if [ -f frontend/.env ]; then
  echo "frontend/.env already exists — leaving it untouched."
else
  cp frontend/.env.example frontend/.env
  # Reuse whatever ended up in .env's API_KEY (just-generated above, or
  # already there from an earlier run) so the two are guaranteed to match —
  # this is the value that has to be identical on both sides for the
  # frontend's X-API-Key header to authenticate against the backend.
  api_key="$(grep '^API_KEY=' .env | cut -d= -f2-)"
  sed -i.bak "s/^VITE_API_KEY=.*/VITE_API_KEY=${api_key}/" frontend/.env && rm -f frontend/.env.bak
  echo "Created frontend/.env with VITE_API_KEY matching the backend's API_KEY."
fi

echo
echo "Setup complete. Your API key (only needed if you're calling the API directly, e.g. with curl):"
grep '^API_KEY=' .env
echo
echo "Next: docker compose up --build -d"
