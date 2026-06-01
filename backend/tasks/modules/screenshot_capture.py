"""
Stage 3 (3.5) — gowitness Screenshot Capture

Captures screenshots of all live hosts using gowitness and stores
the screenshot paths in the Subdomain records.
"""
import logging
import os
import subprocess

from app.models import Subdomain

logger = logging.getLogger(__name__)

GOWITNESS_BIN = '/root/go/bin/gowitness'
GOWITNESS_TIMEOUT = 300  # 5 minutes
SCREENSHOTS_BASE = '/app/screenshots'


def _get_live_host_urls(scan_id: str, db) -> list:
    """Return list of (subdomain_id, url) tuples for alive subdomains."""
    subdomains = (
        db.query(Subdomain)
        .filter(Subdomain.scan_id == scan_id, Subdomain.is_alive == True)  # noqa: E712
        .all()
    )
    result = []
    for s in subdomains:
        host = s.subdomain.strip()
        result.append((s.id, host, f'https://{host}'))
    return result


def run(scan_id: str, db) -> None:
    """
    Stage 3: Screenshot Capture using gowitness.

    - Fetches live hosts from DB
    - Writes URLs to temp file
    - Runs gowitness to capture screenshots
    - Matches screenshots back to subdomain IDs and updates DB
    """
    live_hosts = _get_live_host_urls(scan_id, db)
    if not live_hosts:
        logger.info(f'[{scan_id}] No live hosts for screenshots — skipping')
        return

    logger.info(f'[{scan_id}] Capturing screenshots for {len(live_hosts)} live hosts')
    print(f"[STAGE] screenshot_capture: input={len(live_hosts)} live hosts")

    # Create screenshot directory for this scan
    scan_screenshot_dir = os.path.join(SCREENSHOTS_BASE, scan_id)
    os.makedirs(scan_screenshot_dir, exist_ok=True)

    # Write target URLs to temp file
    tmp_path = f'/tmp/{scan_id}_screenshot_hosts.txt'
    try:
        with open(tmp_path, 'w') as f:
            for _, _, url in live_hosts:
                f.write(url + '\n')

        cmd = [
            GOWITNESS_BIN,
            'scan', 'file',
            '-f', tmp_path,
            '--screenshot-path', scan_screenshot_dir,
            '--screenshot-format', 'png',
            '--write-none',
            '--timeout', '10',
        ]

        logger.info(f'[{scan_id}] Running: {" ".join(cmd)}')

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=GOWITNESS_TIMEOUT,
            env={**os.environ, 'GOWITNESS_HEADLESS': 'true'},
        )

        if proc.returncode != 0:
            logger.warning(f'[{scan_id}] gowitness exited with code {proc.returncode}')
        
        logger.info(f'[{scan_id}] gowitness stdout (first 500 chars): {proc.stdout[:500]}')
        if proc.stderr:
            logger.warning(f'[{scan_id}] gowitness stderr: {proc.stderr[:500]}')

        # gowitness names screenshots after the URL hostname, sanitized
        # Match files to subdomains
        captured = 0
        if os.path.isdir(scan_screenshot_dir):
            screenshot_files = os.listdir(scan_screenshot_dir)
            logger.info(f'[{scan_id}] DIAGNOSTICS: output dir {scan_screenshot_dir} exists.')
            logger.info(f'[{scan_id}] DIAGNOSTICS: discovered {len(screenshot_files)} screenshot file(s) on disk')

            for subdomain_id, host, url in live_hosts:
                # gowitness typically names files like: https-hostname-port-path.png
                host_sanitized = host.replace(':', '-').replace('/', '-').replace('.', '-')
                matched_file = None
                for fname in screenshot_files:
                    if fname.endswith('.png') and f'---{host}-' in fname:
                        matched_file = fname
                        break

                if matched_file:
                    rel_path = f'{scan_id}/{matched_file}'
                    subdomain_obj = db.query(Subdomain).filter(Subdomain.id == subdomain_id).first()
                    if subdomain_obj:
                        subdomain_obj.screenshot_path = rel_path
                        captured += 1

        db.commit()
        
        count = db.query(Subdomain).filter(Subdomain.scan_id == scan_id, Subdomain.screenshot_path != None).count()
        print(f"[STAGE] screenshot_capture: output={count} screenshots")
        print(f"[DB] Verified {count} screenshots committed for scan {scan_id}")

        logger.info(f'[{scan_id}] DIAGNOSTICS: Inserted {captured} screenshot paths into DB')
        logger.info(f'[screenshot_capture] Captured {captured} screenshots')

    except subprocess.TimeoutExpired:
        logger.error(f'[{scan_id}] gowitness timed out after {GOWITNESS_TIMEOUT}s')
        db.commit()
    except FileNotFoundError:
        logger.error(f'[{scan_id}] gowitness binary not found at {GOWITNESS_BIN}')
    except Exception as exc:
        logger.error(f'[{scan_id}] Screenshot capture error: {exc}', exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
