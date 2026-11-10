# Measured project metrics — 2026-11-11

Measured on `codex/step-5-metrics` from the local Windows 11 checkout, with Docker Desktop running the six-service Compose stack and its bundled Juice Shop target. Commands below run from the repository root unless a different directory is shown. These are observations from this checkout, not performance promises for other machines or targets.

| Metric | Measured value |
| --- | ---: |
| Backend tests | 131 passed |
| Backend statement coverage | 80% (1,407 statements; 278 missed) |
| Frontend tests | 21 passed in 4 files |
| Typical Juice Shop scan duration | 132.79 seconds (median of 3 completed local runs) |
| API operations | 19 (18 under `/api/v1`, plus `GET /health`) |
| Intelligence entries | 51 (25 services, 12 technologies, 14 vulnerabilities) |
| Named correlation rules | 6 |

## Reproduce the counts

**Backend tests and coverage.** From `backend/`, with the project dependencies and `pytest-cov` installed:

```powershell
.\venv\Scripts\python.exe -m pytest -q -ra --cov=app --cov-report=term
```

The reported 80% is pytest-cov's rounded **statement** coverage for `app/`; it is not branch coverage. The DB-backed tests start a disposable PostgreSQL container, so Docker Desktop must be available.

**Frontend tests.** From `frontend/`, after `npm ci`:

```powershell
npm test
```

**Juice Shop duration.** Three `force_rescan=true` scans were submitted sequentially to the local API. Each run finished with overall status `completed` and all four scanner stages successful. Duration is the PostgreSQL `updated_at - created_at` interval: it includes queue wait and worker processing, but excludes browser rendering. The median is the middle observed duration, not an estimate. The actual IDs and SQL results are below.

To repeat, submit a scan, wait for its status to reach `completed`, then repeat twice. `API_KEY` remains local in `.env`; do not print or commit it.

```powershell
$apiKey = ((Get-Content .env | Where-Object { $_ -like 'API_KEY=*' } | Select-Object -First 1) -split '=', 2)[1]
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/api/v1/scans/' -Headers @{ 'x-api-key' = $apiKey } -ContentType 'application/json' -Body '{"target":"juice-shop","force_rescan":true}'
```

Check the returned ID with the authenticated `GET /api/v1/scans/{scan_id}/status` endpoint. After three scans finish, use the same SQL measurement as this report; substitute your own three IDs for new runs:

```powershell
docker compose exec -T db psql -U postgres -d argus -A -F ',' -c "SELECT id, status, round(extract(epoch FROM updated_at-created_at)::numeric, 2) AS duration_s FROM scans WHERE id IN ('3c80cb9c-b6ec-4c14-bdeb-33e152dbf413','45db20a4-2c46-44f2-aef6-c7b662e23aee','8ce9db5f-779a-4e59-a6fe-66d57b50553d') ORDER BY created_at"
docker compose exec -T db psql -U postgres -d argus -A -t -c "SELECT round(percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM updated_at-created_at))::numeric, 2) FROM scans WHERE id IN ('3c80cb9c-b6ec-4c14-bdeb-33e152dbf413','45db20a4-2c46-44f2-aef6-c7b662e23aee','8ce9db5f-779a-4e59-a6fe-66d57b50553d') AND status='completed'"
```

| Scan ID | Status | Duration (seconds) |
| --- | --- | ---: |
| `3c80cb9c-b6ec-4c14-bdeb-33e152dbf413` | completed | 165.36 |
| `45db20a4-2c46-44f2-aef6-c7b662e23aee` | completed | 124.95 |
| `8ce9db5f-779a-4e59-a6fe-66d57b50553d` | completed | 132.79 |

Three runs on one local target are a small sample. Scanner templates, network conditions, tool versions, and machine load can change these times. The failed fresh-stack baseline did not produce a valid before/after speed comparison.

**API operations.** Count each published HTTP method and path once from the running development API's OpenAPI document; exclude documentation UI routes and automatic HEAD/OPTIONS methods:

```powershell
python -c "import json,urllib.request; d=json.load(urllib.request.urlopen('http://127.0.0.1:8000/openapi.json')); r=[(m,p) for p,methods in d['paths'].items() for m in methods if m in ('get','post','put','patch','delete')]; print('api_operations',len(r),'api_v1',sum(p.startswith('/api/v1/') for m,p in r))"
```

Output: `api_operations 19 api_v1 18`. The remaining operation is `GET /health`. `/openapi.json` is disabled in production mode, so run this command in the local development stack.

**Intelligence entries.** Validate the source JSON files and compare the three category counts with the running loader's health response:

```powershell
python scripts/validate_intelligence.py
Invoke-RestMethod 'http://127.0.0.1:8000/health' | Select-Object -ExpandProperty intelligence_library
```

The validator reported 51 valid entry files; the API loaded 25 services, 12 technologies, and 14 vulnerabilities.

**Correlation rules.** Count named rule declarations in the current engine source:

```powershell
rg -c 'rule_name="' backend/app/engines/correlation.py
```

Output: `6`. This counts defined rule branches, not how many matched a particular scan.
