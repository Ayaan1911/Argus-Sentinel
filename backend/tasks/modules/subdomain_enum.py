import os
import subprocess
import socket
import logging
from app.models import Subdomain, Scan

logger = logging.getLogger(__name__)

WORDLIST_PATH = '/app/wordlists/subdomains-top1000.txt'

# Fallback short wordlist for when the file isn't available
FALLBACK_WORDS = [
    'www', 'mail', 'ftp', 'smtp', 'pop', 'imap', 'ns1', 'ns2', 'ns3',
    'mx', 'vpn', 'dev', 'staging', 'api', 'admin', 'portal', 'app',
    'blog', 'shop', 'store', 'cdn', 'static', 'assets', 'media',
    'test', 'demo', 'beta', 'alpha', 'm', 'mobile', 'secure', 'web',
    'git', 'gitlab', 'jenkins', 'ci', 'jira', 'confluence', 'dashboard',
    'login', 'auth', 'sso', 'accounts', 'forum', 'support', 'help',
    'status', 'monitor', 'metrics', 'docs', 'wiki', 'old', 'new',
    'internal', 'intranet', 'extranet', 'corp', 'corporate',
]


def load_wordlist() -> list:
    """Load subdomain wordlist from file or fall back to built-in list."""
    if os.path.exists(WORDLIST_PATH):
        try:
            with open(WORDLIST_PATH) as f:
                words = [line.strip() for line in f if line.strip()]
            logger.info(f'Loaded {len(words)} words from wordlist')
            return words
        except OSError as e:
            logger.warning(f'Failed to read wordlist: {e}')
    logger.info(f'Using fallback wordlist ({len(FALLBACK_WORDS)} words)')
    return FALLBACK_WORDS


def run_subfinder(domain: str) -> set:
    """Run subfinder tool for passive subdomain enumeration."""
    results = set()
    try:
        proc = subprocess.run(
            ['subfinder', '-d', domain, '-silent', '-timeout', '30'],
            capture_output=True,
            text=True,
            timeout=180,
        )
        for line in proc.stdout.splitlines():
            line = line.strip().lower()
            if line and domain in line:
                results.add(line)
        logger.info(f'subfinder found {len(results)} subdomains for {domain}')
    except subprocess.TimeoutExpired:
        logger.warning(f'subfinder timed out for {domain}')
    except FileNotFoundError:
        logger.warning('subfinder binary not found, skipping passive enumeration')
    except Exception as e:
        logger.warning(f'subfinder error: {e}')
    return results


def dns_brute_force(domain: str) -> set:
    """DNS brute-force using wordlist."""
    results = set()
    wordlist = load_wordlist()
    resolved = 0

    for word in wordlist:
        fqdn = f'{word}.{domain}'
        try:
            # getaddrinfo is more reliable cross-platform than gethostbyname
            socket.getaddrinfo(fqdn, None)
            results.add(fqdn.lower())
            resolved += 1
        except (socket.gaierror, socket.herror, socket.timeout):
            pass
        except Exception:
            pass

    logger.info(f'DNS brute-force resolved {resolved}/{len(wordlist)} for {domain}')
    return results


def run(scan_id: str, db) -> None:
    """
    Stage 1: Subdomain Enumeration.
    Combines passive (subfinder) and active (DNS brute-force) discovery.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    domain = scan.domain
    logger.info(f'[{scan_id}] Starting subdomain enumeration for {domain}')

    found = set()
    found.add(domain)  # Always include the root domain itself

    # Passive enumeration via subfinder
    found.update(run_subfinder(domain))

    # Active DNS brute-force
    found.update(dns_brute_force(domain))

    # Clear any existing subdomains for this scan (e.g. re-run)
    db.query(Subdomain).filter(Subdomain.scan_id == scan_id).delete()
    db.commit()

    # Persist results
    for sub in sorted(found):
        subdomain = Subdomain(scan_id=scan_id, subdomain=sub)
        db.add(subdomain)
    db.commit()

    logger.info(f'[{scan_id}] Subdomain enumeration complete: {len(found)} subdomains found')
