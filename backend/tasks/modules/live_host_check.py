import subprocess
import json
import logging
import tempfile
import os
import requests
from bs4 import BeautifulSoup
from app.models import Subdomain

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 8
HTTPX_TIMEOUT = 300


def _parse_httpx_line(line: str) -> tuple[str, dict] | None:
    """Parse a single JSON line from httpx output."""
    try:
        data = json.loads(line)
        # httpx can return host under 'input' or 'url'
        raw_host = data.get('input', data.get('url', ''))
        host = (
            raw_host
            .replace('https://', '')
            .replace('http://', '')
            .split('/')[0]
            .split(':')[0]
            .lower()
            .strip()
        )
        if not host:
            return None

        technologies = data.get('tech', data.get('technologies', [])) or []
        if isinstance(technologies, list):
            # Normalize: extract names if they are dicts
            tech_names = []
            for t in technologies:
                if isinstance(t, str):
                    tech_names.append(t)
                elif isinstance(t, dict):
                    tech_names.append(t.get('name', str(t)))
            technologies = tech_names

        return host, {
            'is_alive': True,
            'status_code': data.get('status-code') or data.get('status_code'),
            'title': (data.get('title') or '').strip(),
            'technologies': technologies,
        }
    except (json.JSONDecodeError, AttributeError):
        return None


def _httpx_scan(subdomains: list) -> dict:
    """Run httpx against a list of subdomains, return dict keyed by hostname."""
    results = {}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for s in subdomains:
            f.write(s.subdomain + '\n')
        tmp_path = f.name

    try:
        with open(tmp_path, 'r') as tf:
            print(f"DEBUG: httpx tmp file contents (first 5 lines): {tf.readlines()[:5]}", flush=True)
            
        cmd = [
            '/root/go/bin/httpx',
            '-l', tmp_path,
            '-silent',
            '-status-code',
            '-title',
            '-tech-detect',
            '-follow-redirects',
            '-fc', '400,404,410',
            '-p', '80,443,8080,8443',
            '-H', 'User-Agent: Mozilla/5.0 (compatible; SecurityScanner/1.0)',
            '-json',
            '-timeout', '15',
            '-retries', '3',
        ]
        print(f"DEBUG: Running httpx with cmd: {' '.join(cmd)}", flush=True)
        
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=HTTPX_TIMEOUT,
        )
        if proc.returncode != 0:
            print(f"ERROR: httpx returned non-zero exit code: {proc.returncode}. stderr: {proc.stderr}", flush=True)

        if proc.stderr:
            print(f"WARNING: httpx stderr: {proc.stderr}", flush=True)

        print(f"DEBUG: httpx stdout length: {len(proc.stdout)}", flush=True)

        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parsed = _parse_httpx_line(line)
            if parsed:
                host, info = parsed
                results[host] = info
        
        print(f"DEBUG: httpx total results collected: {len(results)}", flush=True)
        print(f"DEBUG: httpx result keys: {list(results.keys())[:5]}", flush=True)
    except subprocess.TimeoutExpired:
        print('ERROR: httpx global timeout reached', flush=True)
    except FileNotFoundError:
        logger.error('httpx binary not found')
        raise
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return results


def _requests_fallback(subdomains: list) -> dict:
    """Fallback HTTP probe using the requests library when httpx is unavailable."""
    results = {}
    for sub in subdomains:
        for scheme in ('https', 'http'):
            url = f'{scheme}://{sub.subdomain}'
            try:
                resp = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
                title = ''
                try:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    if soup.title and soup.title.string:
                        title = soup.title.string.strip()
                except Exception:
                    pass
                results[sub.subdomain.lower()] = {
                    'is_alive': True,
                    'status_code': resp.status_code,
                    'title': title,
                    'technologies': [],
                }
                break  # Stop at first successful scheme
            except requests.RequestException:
                continue
    return results


def run(scan_id: str, db) -> None:
    """
    Stage 2: Live Host Detection.
    Uses httpx for fast concurrent probing with tech detection.
    Falls back to sequential requests if httpx is unavailable.
    """
    subdomains = db.query(Subdomain).filter(Subdomain.scan_id == scan_id).all()
    if not subdomains:
        logger.info(f'[{scan_id}] No subdomains to probe')
        return

    logger.info(f'[{scan_id}] Probing {len(subdomains)} hosts for liveness')
    print(f"[STAGE] live_host_check: input={len(subdomains)} subdomains")

    # Try httpx first, fall back to requests
    try:
        results = _httpx_scan(subdomains)
        if len(results) == 0:
            logger.info(f'[{scan_id}] Primary live host detection returned 0, trying fallback...')
            results = _requests_fallback(subdomains)
    except FileNotFoundError:
        logger.info(f'[{scan_id}] Falling back to requests for live host check')
        results = _requests_fallback(subdomains)

    # Update subdomain records
    for sub in subdomains:
        info = results.get(sub.subdomain.lower())
        if info:
            sub.is_alive = info['is_alive']
            sub.status_code = info.get('status_code')
            sub.title = info.get('title', '')
            sub.technologies = info.get('technologies', [])
        else:
            sub.is_alive = False
            sub.status_code = None

    db.commit()

    alive_count = db.query(Subdomain).filter(Subdomain.scan_id == scan_id, Subdomain.is_alive == True).count()
    print(f"[STAGE] live_host_check: output={alive_count} live hosts")
    print(f"[DB] Verified {alive_count} live hosts committed for scan {scan_id}")

    logger.info(f'[{scan_id}] Live host detection complete: {alive_count}/{len(subdomains)} alive')
