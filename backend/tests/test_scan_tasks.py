"""
Task orchestration tests for app.tasks.scan_tasks.run_scan — the Celery task
is called directly (bypassing the broker), with each scanner's run()
patched out, against the real throwaway Postgres from conftest.py.
"""
import uuid
from unittest.mock import AsyncMock, patch

from sqlalchemy import text


def _insert_pending_scan(sync_engine, target="example.com", audience="student"):
    scan_id = str(uuid.uuid4())
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO scans (id, target, status, audience, stage_status, created_at) "
                "VALUES (:id, :target, 'pending', :audience, '{}', now())"
            ),
            {"id": scan_id, "target": target, "audience": audience},
        )
    return scan_id


def _fetch_scan(sync_engine, scan_id):
    with sync_engine.begin() as conn:
        row = conn.execute(
            text("SELECT status, stage_status FROM scans WHERE id = :id"),
            {"id": scan_id},
        ).mappings().first()
    return row


def _fetch_finding_count(sync_engine, scan_id):
    with sync_engine.begin() as conn:
        return conn.execute(
            text("SELECT count(*) FROM findings WHERE scan_id = :id"),
            {"id": scan_id},
        ).scalar_one()


def _no_finding(source, ftype, title, raw_data):
    return {"source": source, "type": ftype, "title": title, "raw_data": raw_data}


def test_stage_status_recorded_on_success_for_every_tool(clean_db):
    from app.tasks.scan_tasks import run_scan

    scan_id = _insert_pending_scan(clean_db["sync_engine"])

    with patch("app.scanners.subfinder.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.httpx.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.nmap.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.nuclei.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))):
        run_scan(scan_id, "example.com", "student")

    row = _fetch_scan(clean_db["sync_engine"], scan_id)
    assert row["status"] == "completed"
    stage_status = row["stage_status"]
    for tool in ("subfinder", "httpx", "nmap", "nuclei"):
        assert stage_status[tool] == {"status": "success", "detail": None}


def test_stage_status_records_timeout(clean_db):
    from app.tasks.scan_tasks import run_scan

    scan_id = _insert_pending_scan(clean_db["sync_engine"])
    timeout_status = {"status": "timeout", "detail": "exceeded 300s"}

    with patch("app.scanners.subfinder.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.httpx.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.nmap.run", new=AsyncMock(return_value=([], timeout_status))), \
         patch("app.scanners.nuclei.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))):
        run_scan(scan_id, "example.com", "student")

    row = _fetch_scan(clean_db["sync_engine"], scan_id)
    # A tool timing out doesn't crash the whole scan — it's recorded per-stage.
    assert row["status"] == "completed"
    assert row["stage_status"]["nmap"] == timeout_status


def test_stage_status_records_nonzero_exit_failure(clean_db):
    from app.tasks.scan_tasks import run_scan

    scan_id = _insert_pending_scan(clean_db["sync_engine"])
    failed_status = {"status": "failed", "detail": "exit code 1"}

    with patch("app.scanners.subfinder.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.httpx.run", new=AsyncMock(return_value=([], failed_status))), \
         patch("app.scanners.nmap.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.nuclei.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))):
        run_scan(scan_id, "example.com", "student")

    row = _fetch_scan(clean_db["sync_engine"], scan_id)
    assert row["status"] == "completed"
    assert row["stage_status"]["httpx"] == failed_status


def test_stage_status_records_no_binary(clean_db):
    from app.tasks.scan_tasks import run_scan

    scan_id = _insert_pending_scan(clean_db["sync_engine"])
    no_binary_status = {"status": "no_binary", "detail": "/usr/local/bin/nuclei not found"}

    with patch("app.scanners.subfinder.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.httpx.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.nmap.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.nuclei.run", new=AsyncMock(return_value=([], no_binary_status))):
        run_scan(scan_id, "example.com", "student")

    row = _fetch_scan(clean_db["sync_engine"], scan_id)
    assert row["stage_status"]["nuclei"] == no_binary_status


def test_live_discovered_subdomains_are_passed_to_nmap_and_nuclei(clean_db):
    """Regression guard for the sequential-pipeline fix: subfinder's
    discovered subdomains must only reach nmap/nuclei if httpx confirmed them
    live, and the original target must always be included regardless. nuclei
    specifically gets httpx's confirmed live URL (with scheme) rather than a
    bare hostname, per the port-blindness fix in scan_tasks.py."""
    from app.tasks.scan_tasks import run_scan

    scan_id = _insert_pending_scan(clean_db["sync_engine"])

    subfinder_findings = [
        _no_finding("subfinder", "subdomain", "Subdomain: live.example.com", {"host": "live.example.com"}),
        _no_finding("subfinder", "subdomain", "Subdomain: dead.example.com", {"host": "dead.example.com"}),
    ]
    # Only live.example.com (and the original target) show up as live in httpx.
    httpx_findings = [
        _no_finding("httpx", "technology", "Live Host: http://example.com", {"url": "http://example.com"}),
        _no_finding("httpx", "technology", "Live Host: http://live.example.com", {"url": "http://live.example.com"}),
    ]

    nmap_mock = AsyncMock(return_value=([], {"status": "success", "detail": None}))
    nuclei_mock = AsyncMock(return_value=([], {"status": "success", "detail": None}))

    with patch("app.scanners.subfinder.run", new=AsyncMock(return_value=(subfinder_findings, {"status": "success", "detail": None}))), \
         patch("app.scanners.httpx.run", new=AsyncMock(return_value=(httpx_findings, {"status": "success", "detail": None}))), \
         patch("app.scanners.nmap.run", new=nmap_mock), \
         patch("app.scanners.nuclei.run", new=nuclei_mock):
        run_scan(scan_id, "example.com", "student")

    nmap_mock.assert_awaited_once_with(["example.com", "live.example.com"])
    # nuclei gets httpx's confirmed live URL for each host, not a bare hostname.
    nuclei_mock.assert_awaited_once_with(["http://example.com", "http://live.example.com"])


def test_findings_are_persisted_and_processed(clean_db):
    from app.tasks.scan_tasks import run_scan

    scan_id = _insert_pending_scan(clean_db["sync_engine"])

    nmap_finding = _no_finding("nmap", "port", "Port 22/tcp: ssh", {
        "port": 22, "protocol": "tcp", "state": "open", "service": "ssh",
        "product": "OpenSSH", "version": "9.6", "scripts": {},
        "firewall_restricted": False, "default_port": True,
    })

    with patch("app.scanners.subfinder.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.httpx.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.nmap.run", new=AsyncMock(return_value=([nmap_finding], {"status": "success", "detail": None}))), \
         patch("app.scanners.nuclei.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))):
        run_scan(scan_id, "example.com", "student")

    assert _fetch_finding_count(clean_db["sync_engine"], scan_id) == 1


def test_scan_marked_failed_when_task_raises(clean_db):
    from app.tasks.scan_tasks import run_scan

    scan_id = _insert_pending_scan(clean_db["sync_engine"])

    with patch("app.scanners.subfinder.run", new=AsyncMock(side_effect=RuntimeError("boom"))):
        run_scan(scan_id, "example.com", "student")

    row = _fetch_scan(clean_db["sync_engine"], scan_id)
    assert row["status"] == "failed"
