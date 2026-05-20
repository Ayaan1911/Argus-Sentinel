import logging
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from app.models import Subdomain

logger = logging.getLogger(__name__)

# Module-level cache: scan_id -> {js_url: content}
# This avoids hitting the DB for inter-stage JS content sharing.
_js_cache: dict[str, dict[str, str]] = {}

REQUEST_TIMEOUT = 10
JS_CONTENT_TYPES = (
    'application/javascript',
    'text/javascript',
    'application/x-javascript',
)
MAX_JS_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB cap per JS file


def get_js_cache(scan_id: str) -> dict[str, str]:
    """Return the cached JS files for a given scan. Called by secret_detector and endpoint_miner."""
    return _js_cache.get(scan_id, {})


def _is_js_content_type(content_type: str) -> bool:
    ct = content_type.lower().split(';')[0].strip()
    return ct in JS_CONTENT_TYPES or ct.endswith('javascript')


def _fetch_js(url: str) -> str | None:
    """Fetch a JS file and return its content, or None on failure."""
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, stream=True)
        if resp.status_code != 200:
            return None
        content_type = resp.headers.get('content-type', '')
        # Accept if Content-Type is JS or if URL ends with .js
        if not (_is_js_content_type(content_type) or url.split('?')[0].endswith('.js')):
            return None
        # Enforce size limit
        content = b''
        for chunk in resp.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > MAX_JS_SIZE_BYTES:
                logger.debug(f'JS file too large, truncating: {url}')
                break
        return content.decode('utf-8', errors='replace')
    except requests.RequestException:
        return None


def _extract_js_urls_from_html(base_url: str, html: str) -> list[str]:
    """Parse HTML and extract all script[src] URLs."""
    js_urls = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all('script', src=True):
            src = tag.get('src', '').strip()
            if not src:
                continue
            full_url = urljoin(base_url, src)
            parsed = urlparse(full_url)
            if parsed.scheme in ('http', 'https'):
                js_urls.append(full_url)
    except Exception as e:
        logger.debug(f'HTML parse error for {base_url}: {e}')
    return js_urls


def run(scan_id: str, db) -> None:
    """
    Stage 4: JS File Extraction.
    For each live host, fetches the homepage HTML, extracts <script src> tags,
    then downloads each JS file. Results stored in module-level cache for use
    by the secret_detector and endpoint_miner stages.
    """
    global _js_cache

    live_subs = (
        db.query(Subdomain)
        .filter(Subdomain.scan_id == scan_id, Subdomain.is_alive == True)
        .all()
    )

    js_files: dict[str, str] = {}

    for sub in live_subs:
        page_fetched = False
        for scheme in ('https', 'http'):
            base_url = f'{scheme}://{sub.subdomain}'
            try:
                resp = requests.get(base_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
                if resp.status_code >= 400:
                    continue

                js_urls = _extract_js_urls_from_html(resp.url, resp.text)

                for js_url in js_urls:
                    if js_url in js_files:
                        continue  # Already fetched (shared across subdomains of same domain)
                    content = _fetch_js(js_url)
                    if content:
                        js_files[js_url] = content
                        logger.debug(f'[{scan_id}] Fetched JS: {js_url} ({len(content)} chars)')

                page_fetched = True
                break  # Succeeded on this scheme, move to next subdomain

            except requests.RequestException as e:
                logger.debug(f'[{scan_id}] Failed to fetch {base_url}: {e}')
                continue

        if not page_fetched:
            logger.debug(f'[{scan_id}] Could not fetch {sub.subdomain}')

    _js_cache[scan_id] = js_files
    logger.info(f'[{scan_id}] JS extraction complete: {len(js_files)} JS file(s) cached')
