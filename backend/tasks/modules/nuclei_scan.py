"""
Stage 9 — Nuclei Vulnerability Scanner

Runs ProjectDiscovery Nuclei against all live hosts discovered in the scan.
Parses JSON output and persists VulnerabilityFinding records to PostgreSQL.
"""
import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime

from app.models import Subdomain, VulnerabilityFinding

logger = logging.getLogger(__name__)

NUCLEI_BIN = '/root/go/bin/nuclei'
NUCLEI_TIMEOUT = 600  # 10 minutes max

# Severity ordering for sorting
SEVERITY_ORDER = {
    'critical': 0,
    'high': 1,
    'medium': 2,
    'low': 3,
    'info': 4,
    'unknown': 5,
}


def _get_live_host_urls(scan_id: str, db) -> list:
    """
    Return a list of live host URLs (https/http) from the subdomains table.
    Uses the status_code to detect HTTPS vs HTTP, defaults to https.
    """
    subdomains = (
        db.query(Subdomain)
        .filter(Subdomain.scan_id == scan_id, Subdomain.is_alive == True)  # noqa: E712
        .all()
    )
    urls = []
    for s in subdomains:
        host = s.subdomain.strip()
        # If status_code is known and the code came from HTTP, use http; otherwise https
        # httpx already followed redirects and resolved the real URL, so default https
        urls.append(f'https://{host}')
    return urls


def _parse_nuclei_line(line: str) -> dict | None:
    """
    Parse one JSON line from nuclei -json output.
    Returns a dict of extracted fields, or None on parse failure.
    """
    try:
        data = json.loads(line)
        info = data.get('info', {})

        template_id = data.get('template-id', data.get('templateID', 'unknown'))
        template_name = info.get('name', template_id)
        severity = info.get('severity', 'info').lower()
        host = data.get('host', data.get('ip', ''))
        matched_at = data.get('matched-at', data.get('matched', host))
        description = info.get('description', '')
        remediation = info.get('remediation', '')
        tags = info.get('tags', [])

        # Normalize tags to list of strings
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        elif isinstance(tags, list):
            tags = [str(t).strip() for t in tags if t]
        else:
            tags = []

        if not host or not template_id:
            return None

        return {
            'template_id': template_id,
            'template_name': template_name,
            'severity': severity,
            'host': host,
            'matched_at': matched_at or host,
            'description': description[:2000] if description else None,
            'remediation': remediation[:2000] if remediation else None,
            'tags': tags,
        }
    except (json.JSONDecodeError, AttributeError, KeyError) as exc:
        logger.debug(f'[nuclei_scan] Failed to parse line: {exc}')
        return None


def run(scan_id: str, db) -> None:
    """
    Stage 9: Nuclei Vulnerability Scan.

    - Fetches live host URLs from the database
    - Writes them to a temp file
    - Runs nuclei with severity critical,high,medium
    - Parses JSON output line-by-line
    - Persists VulnerabilityFinding rows
    """
    live_urls = _get_live_host_urls(scan_id, db)
    if not live_urls:
        logger.info(f'[{scan_id}] No live hosts for nuclei scan — skipping')
        return

    logger.info(f'[{scan_id}] Starting nuclei scan against {len(live_urls)} live hosts')
    print(f"[STAGE] nuclei_scan: input={len(live_urls)} live hosts")

    # Write targets to temp file
    tmp_path = f'/tmp/{scan_id}_nuclei_hosts.txt'
    try:
        with open(tmp_path, 'w') as f:
            for url in live_urls:
                f.write(url + '\n')

        cmd = [
            NUCLEI_BIN,
            '-l', tmp_path,
            '-severity', 'critical,high,medium',
            '-json',
            '-silent',
            '-timeout', '10',
            '-retries', '1',
            '-c', '25',          # concurrency
            '-rate-limit', '50', # requests/sec to avoid hammering
        ]

        logger.info(f'[{scan_id}] Running: {" ".join(cmd)}')

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=NUCLEI_TIMEOUT,
        )

        if proc.returncode != 0 and proc.stderr:
            logger.warning(f'[{scan_id}] nuclei stderr: {proc.stderr[:500]}')

        count = 0
        host_counts: dict[str, int] = {}

        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            parsed = _parse_nuclei_line(line)
            if not parsed:
                continue

            finding = VulnerabilityFinding(
                scan_id=scan_id,
                template_id=parsed['template_id'],
                template_name=parsed['template_name'],
                severity=parsed['severity'],
                host=parsed['host'],
                matched_at=parsed['matched_at'],
                description=parsed['description'],
                remediation=parsed['remediation'],
                tags=parsed['tags'],
                created_at=datetime.utcnow(),
            )
            db.add(finding)
            count += 1

            host = parsed['host']
            host_counts[host] = host_counts.get(host, 0) + 1

        db.commit()

        for host, n in host_counts.items():
            logger.info(f'[nuclei_scan] Found {n} vulnerabilities on {host}')

        total_vulns = db.query(VulnerabilityFinding).filter(VulnerabilityFinding.scan_id == scan_id).count()
        print(f"[STAGE] nuclei_scan: output={total_vulns} vulns")
        print(f"[DB] Verified {total_vulns} vulns committed for scan {scan_id}")

        logger.info(f'[{scan_id}] Nuclei scan complete: {count} finding(s) saved')

    except subprocess.TimeoutExpired:
        logger.error(f'[{scan_id}] Nuclei timed out after {NUCLEI_TIMEOUT}s')
        db.commit()
    except FileNotFoundError:
        logger.error(f'[{scan_id}] Nuclei binary not found at {NUCLEI_BIN}')
    except Exception as exc:
        logger.error(f'[{scan_id}] Nuclei scan error: {exc}', exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
