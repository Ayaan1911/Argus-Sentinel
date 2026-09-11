"""
API route tests (scans.py, findings.py, intelligence.py) against a real
throwaway Postgres container — see conftest.py for how that's wired up.
Celery dispatch (run_scan.delay) is mocked in every test that creates a scan,
so these tests never need a live Redis/worker.
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings


def _create_scan_row(sync_engine, target, status, created_at=None, audience="student"):
    """Insert a Scan row directly via SQL, bypassing the API, so dedup/recency
    tests can set up prior state precisely."""
    import uuid
    from sqlalchemy import text

    scan_id = str(uuid.uuid4())
    created_at = created_at or datetime.utcnow()
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO scans (id, target, status, audience, stage_status, created_at) "
                "VALUES (:id, :target, :status, :audience, '{}', :created_at)"
            ),
            {"id": scan_id, "target": target, "status": status, "audience": audience, "created_at": created_at},
        )
    return scan_id


def _create_finding_row(sync_engine, scan_id, type_="port", title="Port 22/tcp: ssh",
                         severity="low", confidence=0.9, risk_score=3.0, final_risk_score=None):
    """Insert a Finding row directly via SQL — diff tests need precise control
    over risk_score/severity/confidence across two scans of the same target."""
    import uuid
    from sqlalchemy import text

    finding_id = str(uuid.uuid4())
    final_risk_score = risk_score if final_risk_score is None else final_risk_score
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO findings (id, scan_id, type, title, severity, confidence, risk_score, "
                "final_risk_score, correlation_modifier) "
                "VALUES (:id, :scan_id, :type, :title, :severity, :confidence, :risk_score, "
                ":final_risk_score, 0.0)"
            ),
            {
                "id": finding_id, "scan_id": scan_id, "type": type_, "title": title,
                "severity": severity, "confidence": confidence,
                "risk_score": risk_score, "final_risk_score": final_risk_score,
            },
        )
    return finding_id


# --- Auth ---

def test_create_scan_without_api_key_is_401(client):
    r = client.post("/api/v1/scans/", json={"target": "example.com"})
    assert r.status_code == 401


def test_create_scan_with_wrong_api_key_is_401(client):
    r = client.post("/api/v1/scans/", json={"target": "example.com"}, headers={"x-api-key": "wrong"})
    assert r.status_code == 401


def test_list_scans_without_api_key_is_401(client):
    r = client.get("/api/v1/scans/")
    assert r.status_code == 401


def test_intelligence_without_api_key_is_401(client):
    r = client.get("/api/v1/intelligence/services")
    assert r.status_code == 401


def test_intelligence_with_api_key_is_200(client, auth_headers):
    r = client.get("/api/v1/intelligence/services", headers=auth_headers)
    assert r.status_code == 200


def test_findings_without_api_key_is_401(client):
    r = client.get("/api/v1/findings/scan/11111111-1111-1111-1111-111111111111")
    assert r.status_code == 401


# --- SSRF validation ---

@pytest.mark.parametrize("target", [
    "127.0.0.1",
    "localhost",
    "169.254.169.254",  # cloud metadata address
    "10.0.0.5",
    "192.168.1.1",
    "172.16.0.1",
])
def test_create_scan_rejects_disallowed_targets(client, auth_headers, target):
    r = client.post("/api/v1/scans/", json={"target": target}, headers=auth_headers)
    assert r.status_code == 422


def test_create_scan_allows_juice_shop(client, auth_headers):
    with patch("app.routers.scans.run_scan") as mock_run_scan:
        r = client.post("/api/v1/scans/", json={"target": "juice-shop"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["target"] == "juice-shop"
    mock_run_scan.delay.assert_called_once()


# --- Happy-path CRUD ---

def test_create_scan_happy_path(client, auth_headers):
    with patch("app.routers.scans.run_scan") as mock_run_scan:
        r = client.post("/api/v1/scans/", json={"target": "example.com", "audience": "pentester"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["target"] == "example.com"
    assert body["audience"] == "pentester"
    assert body["status"] == "pending"
    assert body["findings"] == []
    mock_run_scan.delay.assert_called_once_with(body["id"], "example.com", "pentester")


def test_create_scan_normalizes_target(client, auth_headers):
    with patch("app.routers.scans.run_scan"):
        r = client.post("/api/v1/scans/", json={"target": "EXAMPLE.com:8080/path"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["target"] == "example.com"


def test_list_scans(client, auth_headers):
    with patch("app.routers.scans.run_scan"):
        client.post("/api/v1/scans/", json={"target": "example.com"}, headers=auth_headers)
        client.post("/api/v1/scans/", json={"target": "another.com"}, headers=auth_headers)

    r = client.get("/api/v1/scans/", headers=auth_headers)
    assert r.status_code == 200
    targets = {s["target"] for s in r.json()}
    assert targets == {"example.com", "another.com"}


def test_get_scan_not_found(client, auth_headers):
    r = client.get("/api/v1/scans/11111111-1111-1111-1111-111111111111", headers=auth_headers)
    assert r.status_code == 404


def test_delete_scan(client, auth_headers):
    with patch("app.routers.scans.run_scan"):
        create_res = client.post("/api/v1/scans/", json={"target": "example.com"}, headers=auth_headers)
    scan_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/scans/{scan_id}", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json() == {"deleted": True}

    get_res = client.get(f"/api/v1/scans/{scan_id}", headers=auth_headers)
    assert get_res.status_code == 404


def test_scan_status_endpoint_lightweight_fields(client, auth_headers):
    with patch("app.routers.scans.run_scan"):
        create_res = client.post("/api/v1/scans/", json={"target": "example.com", "audience": "developer"}, headers=auth_headers)
    scan_id = create_res.json()["id"]

    r = client.get(f"/api/v1/scans/{scan_id}/status", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["target"] == "example.com"
    assert body["audience"] == "developer"
    assert body["status"] == "pending"
    assert body["stage_status"] == {}
    assert body["finding_count"] == 0


# --- Duplicate-scan guard ---

def test_duplicate_pending_scan_returns_existing(client, auth_headers, clean_db):
    existing_id = _create_scan_row(clean_db["sync_engine"], "example.com", "pending")

    with patch("app.routers.scans.run_scan") as mock_run_scan:
        r = client.post("/api/v1/scans/", json={"target": "example.com"}, headers=auth_headers)

    assert r.status_code == 200
    assert r.json()["id"] == existing_id
    mock_run_scan.delay.assert_not_called()


def test_duplicate_recent_completed_scan_returns_existing(client, auth_headers, clean_db):
    existing_id = _create_scan_row(
        clean_db["sync_engine"], "example.com", "completed",
        created_at=datetime.utcnow() - timedelta(hours=1),
    )

    with patch("app.routers.scans.run_scan") as mock_run_scan:
        r = client.post("/api/v1/scans/", json={"target": "example.com"}, headers=auth_headers)

    assert r.status_code == 200
    assert r.json()["id"] == existing_id
    mock_run_scan.delay.assert_not_called()


def test_old_completed_scan_is_not_reused(client, auth_headers, clean_db):
    old_id = _create_scan_row(
        clean_db["sync_engine"], "example.com", "completed",
        created_at=datetime.utcnow() - timedelta(hours=25),
    )

    with patch("app.routers.scans.run_scan") as mock_run_scan:
        r = client.post("/api/v1/scans/", json={"target": "example.com"}, headers=auth_headers)

    assert r.status_code == 200
    assert r.json()["id"] != old_id
    mock_run_scan.delay.assert_called_once()


def test_force_rescan_bypasses_recent_completed_reuse(client, auth_headers, clean_db):
    existing_id = _create_scan_row(
        clean_db["sync_engine"], "example.com", "completed",
        created_at=datetime.utcnow() - timedelta(hours=1),
    )

    with patch("app.routers.scans.run_scan") as mock_run_scan:
        r = client.post(
            "/api/v1/scans/",
            json={"target": "example.com", "force_rescan": True},
            headers=auth_headers,
        )

    assert r.status_code == 200
    assert r.json()["id"] != existing_id
    mock_run_scan.delay.assert_called_once()


# --- Scan history for a target ---

def test_scan_history_lists_only_completed_scans_newest_first(client, auth_headers, clean_db):
    sync_engine = clean_db["sync_engine"]
    old_id = _create_scan_row(sync_engine, "example.com", "completed", created_at=datetime.utcnow() - timedelta(days=2))
    new_id = _create_scan_row(sync_engine, "example.com", "completed", created_at=datetime.utcnow() - timedelta(days=1))
    _create_scan_row(sync_engine, "example.com", "running", created_at=datetime.utcnow())  # excluded
    _create_scan_row(sync_engine, "other.com", "completed", created_at=datetime.utcnow())  # different target, excluded
    _create_finding_row(sync_engine, new_id)
    _create_finding_row(sync_engine, new_id)

    r = client.get("/api/v1/scans/target/example.com/history", headers=auth_headers)

    assert r.status_code == 200
    body = r.json()
    assert [s["id"] for s in body] == [new_id, old_id]
    assert set(body[0].keys()) == {"id", "created_at", "status", "finding_count"}
    assert body[0]["finding_count"] == 2
    assert body[1]["finding_count"] == 0


def test_scan_history_empty_for_unknown_target(client, auth_headers):
    r = client.get("/api/v1/scans/target/never-scanned.com/history", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


# --- Scan diff ---

def test_diff_defaults_to_most_recent_prior_completed_scan(client, auth_headers, clean_db):
    sync_engine = clean_db["sync_engine"]
    scan_old = _create_scan_row(sync_engine, "example.com", "completed", created_at=datetime.utcnow() - timedelta(days=2))
    scan_mid = _create_scan_row(sync_engine, "example.com", "completed", created_at=datetime.utcnow() - timedelta(days=1))
    scan_new = _create_scan_row(sync_engine, "example.com", "completed", created_at=datetime.utcnow())

    _create_finding_row(sync_engine, scan_old, title="Port 22/tcp: ssh", risk_score=3.0, severity="low")

    _create_finding_row(sync_engine, scan_mid, title="Port 22/tcp: ssh", risk_score=3.0, severity="low")
    _create_finding_row(sync_engine, scan_mid, title="Port 80/tcp: http", risk_score=2.0, severity="informational")

    _create_finding_row(sync_engine, scan_new, title="Port 22/tcp: ssh", risk_score=7.5, severity="high")
    _create_finding_row(sync_engine, scan_new, title="Port 3000/tcp: node", risk_score=4.0, severity="low")

    r = client.get(f"/api/v1/scans/{scan_new}/diff", headers=auth_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["scan_id"] == scan_new
    assert body["compared_to_scan_id"] == scan_mid  # most recent prior, not scan_old
    assert body["target"] == "example.com"
    assert body["summary"] == {"new": 1, "resolved": 1, "changed": 1, "unchanged": 0}
    assert body["new_findings"][0]["title"] == "Port 3000/tcp: node"
    assert body["resolved_findings"][0]["title"] == "Port 80/tcp: http"
    changed = body["changed_findings"][0]
    assert changed["finding"]["title"] == "Port 22/tcp: ssh"
    assert changed["finding"]["final_risk_score"] == 7.5
    assert changed["previous_risk_score"] == 3.0
    assert changed["previous_severity"] == "low"


def test_diff_explicit_compare_to_overrides_default(client, auth_headers, clean_db):
    sync_engine = clean_db["sync_engine"]
    scan_old = _create_scan_row(sync_engine, "example.com", "completed", created_at=datetime.utcnow() - timedelta(days=2))
    scan_mid = _create_scan_row(sync_engine, "example.com", "completed", created_at=datetime.utcnow() - timedelta(days=1))
    scan_new = _create_scan_row(sync_engine, "example.com", "completed", created_at=datetime.utcnow())

    _create_finding_row(sync_engine, scan_old, title="Port 22/tcp: ssh", risk_score=3.0)
    _create_finding_row(sync_engine, scan_mid, title="Port 22/tcp: ssh", risk_score=3.0)
    _create_finding_row(sync_engine, scan_mid, title="Port 80/tcp: http", risk_score=2.0)
    _create_finding_row(sync_engine, scan_new, title="Port 22/tcp: ssh", risk_score=7.5)

    r = client.get(f"/api/v1/scans/{scan_new}/diff?compare_to={scan_old}", headers=auth_headers)

    assert r.status_code == 200
    body = r.json()
    assert body["compared_to_scan_id"] == scan_old
    # Against scan_old, "Port 80/tcp: http" was never there, so nothing resolves.
    assert body["summary"] == {"new": 0, "resolved": 0, "changed": 1, "unchanged": 0}


def test_diff_404_when_no_prior_scan_to_compare_against(client, auth_headers, clean_db):
    scan_id = _create_scan_row(clean_db["sync_engine"], "example.com", "completed")

    r = client.get(f"/api/v1/scans/{scan_id}/diff", headers=auth_headers)

    assert r.status_code == 404


def test_diff_default_never_picks_a_scan_newer_than_the_one_being_diffed(client, auth_headers, clean_db):
    # Regression guard: the oldest scan of a target has no *prior* scan to
    # compare against, even though newer scans of the same target exist —
    # "no compare_to given" must not silently fall back to "the newest scan
    # overall" when that newest scan is actually newer than scan_id itself.
    sync_engine = clean_db["sync_engine"]
    oldest = _create_scan_row(sync_engine, "example.com", "completed", created_at=datetime.utcnow() - timedelta(days=2))
    _create_scan_row(sync_engine, "example.com", "completed", created_at=datetime.utcnow())

    r = client.get(f"/api/v1/scans/{oldest}/diff", headers=auth_headers)

    assert r.status_code == 404


def test_diff_400_when_scan_id_not_found(client, auth_headers):
    r = client.get("/api/v1/scans/11111111-1111-1111-1111-111111111111/diff", headers=auth_headers)
    assert r.status_code == 400


def test_diff_400_when_compare_to_not_found(client, auth_headers, clean_db):
    scan_id = _create_scan_row(clean_db["sync_engine"], "example.com", "completed")

    r = client.get(
        f"/api/v1/scans/{scan_id}/diff?compare_to=11111111-1111-1111-1111-111111111111",
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_diff_400_when_primary_scan_not_completed(client, auth_headers, clean_db):
    sync_engine = clean_db["sync_engine"]
    scan_id = _create_scan_row(sync_engine, "example.com", "running")
    other_id = _create_scan_row(sync_engine, "example.com", "completed")

    r = client.get(f"/api/v1/scans/{scan_id}/diff?compare_to={other_id}", headers=auth_headers)
    assert r.status_code == 400


def test_diff_400_when_compare_to_not_completed(client, auth_headers, clean_db):
    sync_engine = clean_db["sync_engine"]
    scan_id = _create_scan_row(sync_engine, "example.com", "completed")
    other_id = _create_scan_row(sync_engine, "example.com", "pending")

    r = client.get(f"/api/v1/scans/{scan_id}/diff?compare_to={other_id}", headers=auth_headers)
    assert r.status_code == 400


def test_diff_400_when_targets_differ(client, auth_headers, clean_db):
    sync_engine = clean_db["sync_engine"]
    scan_id = _create_scan_row(sync_engine, "example.com", "completed")
    other_id = _create_scan_row(sync_engine, "another.com", "completed")

    r = client.get(f"/api/v1/scans/{scan_id}/diff?compare_to={other_id}", headers=auth_headers)
    assert r.status_code == 400


def test_diff_without_api_key_is_401(client):
    r = client.get("/api/v1/scans/11111111-1111-1111-1111-111111111111/diff")
    assert r.status_code == 401


# --- Demo mode (DEMO_MODE=True) ---
# These monkeypatch the already-imported `settings` singleton directly
# (routers/schemas read its attributes at call time, not import time), and
# never need a live Redis (see module docstring) — Redis is replaced with a
# minimal fake in every test that exercises the demo scan-count ceiling.

def _fake_redis_class(start_count: int = 0):
    state = {"count": start_count}
    fake_client = MagicMock()

    async def _incr(key):
        state["count"] += 1
        return state["count"]

    fake_client.incr = _incr
    fake_client.expire = AsyncMock()
    fake_client.aclose = AsyncMock()

    fake_cls = MagicMock()
    fake_cls.from_url = MagicMock(return_value=fake_client)
    return fake_cls


def test_demo_mode_rejects_real_domain_target(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "DEMO_API_KEY", auth_headers["x-api-key"])

    with patch("app.routers.scans.Redis", _fake_redis_class()):
        r = client.post("/api/v1/scans/", json={"target": "example.com"}, headers=auth_headers)

    assert r.status_code == 422


def test_demo_mode_rejects_previously_allowed_private_ip_too(client, auth_headers, monkeypatch):
    # Sanity check the inversion is total: a target that would normally be
    # rejected for a *different* reason (private IP) still gets rejected —
    # this isn't "only newly-invalid targets get caught," everything except
    # juice-shop is invalid in demo mode, full stop.
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "DEMO_API_KEY", auth_headers["x-api-key"])

    with patch("app.routers.scans.Redis", _fake_redis_class()):
        r = client.post("/api/v1/scans/", json={"target": "10.0.0.5"}, headers=auth_headers)

    assert r.status_code == 422


def test_demo_mode_still_allows_juice_shop(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "DEMO_API_KEY", auth_headers["x-api-key"])

    with patch("app.routers.scans.run_scan") as mock_run_scan, \
         patch("app.routers.scans.Redis", _fake_redis_class()):
        r = client.post("/api/v1/scans/", json={"target": "juice-shop"}, headers=auth_headers)

    assert r.status_code == 200
    assert r.json()["target"] == "juice-shop"
    mock_run_scan.delay.assert_called_once()


def test_demo_mode_requires_the_demo_api_key_not_the_normal_one(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "DEMO_API_KEY", "the-public-demo-key")

    with patch("app.routers.scans.Redis", _fake_redis_class()):
        # The normal API key (auth_headers) no longer works once demo mode is on...
        r_wrong = client.post(
            "/api/v1/scans/", json={"target": "juice-shop"},
            headers=auth_headers,
        )
        # ...only the published demo key does.
        with patch("app.routers.scans.run_scan"):
            r_right = client.post(
                "/api/v1/scans/", json={"target": "juice-shop"},
                headers={"x-api-key": "the-public-demo-key"},
            )

    assert r_wrong.status_code == 401
    assert r_right.status_code == 200


def test_demo_scan_ceiling_raises_429_once_exceeded(monkeypatch):
    import asyncio
    from fastapi import HTTPException
    from app.routers.scans import _enforce_demo_scan_ceiling

    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "DEMO_SCAN_DAILY_LIMIT", 2)

    with patch("app.routers.scans.Redis", _fake_redis_class()):
        asyncio.run(_enforce_demo_scan_ceiling())  # count -> 1, within limit
        asyncio.run(_enforce_demo_scan_ceiling())  # count -> 2, within limit
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(_enforce_demo_scan_ceiling())  # count -> 3, over limit

    assert exc_info.value.status_code == 429
    assert "daily" in exc_info.value.detail.lower()


def test_demo_scan_ceiling_is_a_noop_when_demo_mode_off(monkeypatch):
    import asyncio
    from app.routers.scans import _enforce_demo_scan_ceiling

    monkeypatch.setattr(settings, "DEMO_MODE", False)

    # Deliberately not mocking Redis here: if this ever touched Redis while
    # demo mode is off, it would hang/fail against the real (unreachable
    # from the test host) Redis URL instead of returning immediately.
    asyncio.run(_enforce_demo_scan_ceiling())


def test_demo_mode_off_by_default_uses_normal_rate_limit():
    assert settings.DEMO_MODE is False
    from app.routers.scans import _scan_rate_limit
    assert _scan_rate_limit() == "5/minute"
