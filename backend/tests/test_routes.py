"""
API route tests (scans.py, findings.py, intelligence.py) against a real
throwaway Postgres container — see conftest.py for how that's wired up.
Celery dispatch (run_scan.delay) is mocked in every test that creates a scan,
so these tests never need a live Redis/worker.
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


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
