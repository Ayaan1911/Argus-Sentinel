import re
import logging
from app.models import Endpoint
from .js_extractor import get_js_cache

logger = logging.getLogger(__name__)

MAX_URL_LENGTH = 500
MAX_ENDPOINTS_PER_SCAN = 5000  # Guard against extremely noisy JS

# Matches quoted API-style paths starting with /api, /v1, /graphql, etc.
API_PATH_PATTERN = re.compile(
    r'[\'"`]'
    r'(\/(?:api|v\d+|graphql|rest|rpc|endpoint|auth|oauth|token|'
    r'user|users|account|accounts|admin|login|logout|register|signup|'
    r'webhook|internal|private|public|health|status|metrics|ping|'
    r'upload|download|search|query|data|config|settings|profile|'
    r'dashboard|report|reports|audit|logs|events|notifications|'
    r'payment|checkout|cart|order|orders|product|products|'
    r'subscription|billing|invoice|invoices|team|teams|org|'
    r'organization|workspace|project|projects|task|tasks|'
    r'message|messages|chat|feed|timeline|activity)'
    r'[\w\-\/\.\?\=\&\#\%\+@:]*)'
    r'[\'"`]',
    re.IGNORECASE,
)

# Matches full HTTP/HTTPS URLs embedded in JS
FULL_URL_PATTERN = re.compile(
    r'(?<![\'"`\\])'          # Not prefixed by quote (avoid double-counting)
    r'(https?://[\w\-\.]+(?:/[\w\-\.\/\?\=\&\#\%\+@:]*)?)',
    re.IGNORECASE,
)

# Matches fetch()/axios()/XMLHttpRequest-style call patterns to extract paths
FETCH_PATTERN = re.compile(
    r'(?:fetch|axios(?:\.get|\.post|\.put|\.delete|\.patch)?|'
    r'xhr\.open|request|http\.get|http\.post)\s*\(\s*[\'"`]'
    r'(\/[^\s\'"`]{2,}|https?://[^\s\'"`]{5,})'
    r'[\'"`]',
    re.IGNORECASE,
)


def run(scan_id: str, db) -> None:
    """
    Stage 6: Endpoint Mining.
    Analyzes cached JS files to extract:
    - API path strings (quoted paths starting with known prefixes)
    - Full HTTP/HTTPS URLs embedded in code
    - fetch()/axios()/XHR call argument URLs
    Deduplicates and stores results in the endpoints table.
    """
    js_files = get_js_cache(scan_id)
    if not js_files:
        logger.info(f'[{scan_id}] No JS files in cache, skipping endpoint mining')
        return

    print(f"[STAGE] endpoint_miner: input={len(js_files)} JS files")
    seen: set[str] = set()
    count = 0

    def add_endpoint(url: str, source: str) -> None:
        nonlocal count
        url = url.strip()
        if not url or url in seen or len(url) > MAX_URL_LENGTH:
            return
        if count >= MAX_ENDPOINTS_PER_SCAN:
            return
        seen.add(url)
        db.add(Endpoint(scan_id=scan_id, url=url, source_file=source))
        count += 1

    for file_url, content in js_files.items():
        # Extract API path strings
        for match in API_PATH_PATTERN.findall(content):
            add_endpoint(match, file_url)

        # Extract full URLs
        for match in FULL_URL_PATTERN.findall(content):
            add_endpoint(match, file_url)

        # Extract fetch/axios/XHR call arguments
        for match in FETCH_PATTERN.findall(content):
            add_endpoint(match, file_url)

    db.commit()
    
    total_endpoints = db.query(Endpoint).filter(Endpoint.scan_id == scan_id).count()
    print(f"[STAGE] endpoint_miner: output={total_endpoints} endpoints")
    print(f"[DB] Verified {total_endpoints} endpoints committed for scan {scan_id}")
    
    logger.info(f'[{scan_id}] Endpoint mining complete: {count} endpoint(s) discovered')
