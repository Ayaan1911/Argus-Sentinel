"""
Task orchestration tests for app.tasks.scan_tasks.run_scan — the Celery task
is called directly (bypassing the broker), with each scanner's run()
patched out, against the real throwaway Postgres from conftest.py.
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from sqlalchemy import text


def _insert_pending_scan(sync_engine, target="example.com", audience="student", is_demo=False, created_at=None):
    scan_id = str(uuid.uuid4())
    created_at = created_at or datetime.now(timezone.utc)
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO scans (id, target, status, audience, stage_status, is_demo, created_at) "
                "VALUES (:id, :target, 'pending', :audience, '{}', :is_demo, :created_at)"
            ),
            {"id": scan_id, "target": target, "audience": audience, "is_demo": is_demo, "created_at": created_at},
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


def _insert_finding(sync_engine, scan_id, title="Test Finding"):
    finding_id = str(uuid.uuid4())
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO findings (id, scan_id, type, title, severity, confidence, risk_score, final_risk_score) "
                "VALUES (:id, :scan_id, 'port', :title, 'low', 1.0, 2.0, 2.0)"
            ),
            {"id": finding_id, "scan_id": scan_id, "title": title},
        )
    return finding_id


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


def test_prune_demo_scans_deletes_only_expired_demo_scans(clean_db):
    from app.tasks.scan_tasks import prune_demo_scans

    sync_engine = clean_db["sync_engine"]
    now = datetime.now(timezone.utc)

    old_demo_id = _insert_pending_scan(sync_engine, is_demo=True, created_at=now - timedelta(hours=25))
    _insert_finding(sync_engine, old_demo_id)
    fresh_demo_id = _insert_pending_scan(sync_engine, is_demo=True, created_at=now - timedelta(hours=1))
    old_real_id = _insert_pending_scan(sync_engine, is_demo=False, created_at=now - timedelta(hours=25))

    result = prune_demo_scans()

    assert result == {"pruned": 1}
    assert _fetch_scan(sync_engine, old_demo_id) is None
    assert _fetch_finding_count(sync_engine, old_demo_id) == 0
    assert _fetch_scan(sync_engine, fresh_demo_id) is not None
    assert _fetch_scan(sync_engine, old_real_id) is not None


def test_prune_demo_scans_is_a_noop_with_nothing_expired(clean_db):
    from app.tasks.scan_tasks import prune_demo_scans

    sync_engine = clean_db["sync_engine"]
    fresh_demo_id = _insert_pending_scan(sync_engine, is_demo=True, created_at=datetime.now(timezone.utc))

    result = prune_demo_scans()

    assert result == {"pruned": 0}
    assert _fetch_scan(sync_engine, fresh_demo_id) is not None


def _fetch_findings(sync_engine, scan_id):
    with sync_engine.begin() as conn:
        rows = conn.execute(
            text("SELECT title, risk_score, correlation_modifier, final_risk_score, reasoning_breakdown "
                 "FROM findings WHERE scan_id = :id"),
            {"id": scan_id},
        ).mappings().all()
    return {r["title"]: r for r in rows}


def test_correlation_modifier_is_persisted(clean_db):
    """Plumbing guard: a finding that must trigger a correlation rule has
    that rule's modifier in its stored correlation_modifier, final_risk_score
    AND reasoning_breakdown — i.e. what the API and frontend actually read."""
    from app.tasks.scan_tasks import run_scan

    scan_id = _insert_pending_scan(clean_db["sync_engine"])
    admin = _no_finding("httpx", "technology", "Live Host: http://example.com/admin",
                        {"url": "http://example.com/admin", "admin_panel_exposed": True})

    with patch("app.scanners.subfinder.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.httpx.run", new=AsyncMock(return_value=([admin], {"status": "success", "detail": None}))), \
         patch("app.scanners.nmap.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))), \
         patch("app.scanners.nuclei.run", new=AsyncMock(return_value=([], {"status": "success", "detail": None}))):
        run_scan(scan_id, "example.com", "student")

    row = _fetch_findings(clean_db["sync_engine"], scan_id)["Live Host: http://example.com/admin"]
    assert row["correlation_modifier"] == 1.5
    assert row["final_risk_score"] == row["risk_score"] + 1.5
    assert any(b["label"] == "Correlation: admin_panel_exposed" for b in row["reasoning_breakdown"])


# Real tool output captured from live runs (2026-09-23): the SSH script output
# and nuclei record are verbatim from a real scanme.nmap.org scan, the
# redis-info output is verbatim from nmap against an auth-less Redis.
_REAL_NMAP_XML = """<?xml version="1.0"?>
<nmaprun><host><status state="up"/>
<address addr="45.33.32.156" addrtype="ipv4"/>
<ports>
<port protocol="tcp" portid="22"><state state="open"/>
<service name="ssh" product="OpenSSH" version="6.6.1p1 Ubuntu 2ubuntu2.13"/>
<script id="ssh-auth-methods" output="&#xa;  Supported authentication methods: &#xa;    publickey&#xa;    password"/></port>
<port protocol="tcp" portid="80"><state state="open"/>
<service name="http" product="Apache httpd" version="2.4.7"/></port>
<port protocol="tcp" portid="6379"><state state="open"/>
<service name="redis" product="Redis key-value store" version="7.4.9"/>
<script id="redis-info" output="&#xa;  Version: 7.4.9&#xa;  Operating System: Linux 6.6.114.1-microsoft-standard-WSL2 x86_64&#xa;  Architecture: 64 bits&#xa;  Role: master"/></port>
</ports></host></nmaprun>"""

_REAL_NUCLEI_LINE = (
    '{"template-id": "apache-mod-negotiation-listing", "info": {"name": "Apache mod_negotiation - Pseudo Directory Listing", '
    '"tags": ["apache", "misconfig", "exposure", "mod-negotiation"], "severity": "low"}, "type": "http", '
    '"host": "example.com", "matched-at": "http://example.com/index", "ip": "45.33.32.156"}'
)

_HTTPX_LINES = "\n".join([
    '{"url": "http://example.com", "title": "Go ahead and ScanMe!", "status_code": 200, "tech": ["Apache HTTP Server:2.4.7", "Ubuntu"]}',
    '{"url": "http://example.com:8080", "title": "Admin Login", "status_code": 200, "tech": ["Apache HTTP Server:2.4.7"]}',
])


def _subprocess_output(stdout):
    return AsyncMock(return_value=(stdout, "", {"status": "success", "detail": None}))


def test_every_correlation_rule_fires_through_the_real_pipeline(clean_db, caplog):
    """Real scanner parsers + processor + correlation + DB, with only the
    tool subprocesses and DNS lookups faked. Every remaining rule must come
    out the other end as a stored, nonzero modifier (or, for the scan-wide
    multiple_high_severity rule, in the engine's matched-rules log line)."""
    import logging
    from app.tasks.scan_tasks import run_scan

    scan_id = _insert_pending_scan(clean_db["sync_engine"])
    dns_a = {"legacy-app.herokuapp.com": None}  # CNAME target gone -> dangling
    with patch("app.scanners.subfinder.run_subprocess", new=_subprocess_output("legacy.example.com\n")), \
         patch("app.scanners.subfinder._resolve_a", side_effect=lambda h: dns_a.get(h)), \
         patch("app.scanners.subfinder._resolve_cname",
               side_effect=lambda h: "legacy-app.herokuapp.com" if h == "legacy.example.com" else None), \
         patch("app.scanners.httpx.run_subprocess", new=_subprocess_output(_HTTPX_LINES)), \
         patch("app.scanners.nmap.run_subprocess", new=_subprocess_output(_REAL_NMAP_XML)), \
         patch("app.scanners.nuclei.run_subprocess", new=_subprocess_output(_REAL_NUCLEI_LINE)), \
         caplog.at_level(logging.INFO, logger="app.tasks.scan_tasks"):
        run_scan(scan_id, "example.com", "student")

    rows = _fetch_findings(clean_db["sync_engine"], scan_id)

    def corr(title):
        return {b["label"].removeprefix("Correlation: "): b["modifier"]
                for b in rows[title]["reasoning_breakdown"] if b["label"].startswith("Correlation: ")}

    assert corr("Port 6379/tcp: redis") == {"open_database_no_auth": 3.0}
    assert corr("Port 22/tcp: ssh") == {"internet_facing_ssh_weak_auth": 2.5}
    assert corr("Apache mod_negotiation - Pseudo Directory Listing: http://example.com/index") == {"outdated_stack_with_vuln": 2.0}
    assert corr("Live Host: http://example.com:8080") == {"admin_panel_exposed": 1.5}
    assert corr("Subdomain: legacy.example.com") == {"subdomain_takeover_critical": 3.0}
    assert rows["Port 6379/tcp: redis"]["correlation_modifier"] == 3.0
    assert "multiple_high_severity" in caplog.text
