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

    def prioritize_subdomains(subdomains_list, limit=150):
        import random
        # Priority tiers - pick from each tier in order
        high_priority_keywords = {
            'api', 'www', 'app', 'admin', 'mail', 'smtp', 'ftp',
            'dev', 'staging', 'prod', 'portal', 'dashboard', 'login',
            'auth', 'sso', 'cdn', 'static', 'assets', 'media',
            'docs', 'help', 'support', 'status', 'monitor',
            'vpn', 'remote', 'git', 'jira', 'jenkins', 'gitlab',
            'raw', 'gist', 'pages', 'shop', 'store', 'blog'
        }
        
        # Filter out obvious garbage (pure numbers, very long random strings)
        def is_quality_subdomain(sub):
            # Extract the leftmost label
            label = sub.split('.')[0].lower()
            # Skip pure numeric labels
            if label.isdigit():
                return False
            # Skip very short random-looking labels (1-2 chars are ok: 'mx', 'ns')
            # Skip labels that look like hashes (long hex strings)
            if len(label) > 20 and all(c in '0123456789abcdef-' for c in label):
                return False
            return True
        
        quality = [s for s in subdomains_list if is_quality_subdomain(s)]
        
        # Tier 1: high priority keywords (exact match on first label)
        tier1 = [s for s in quality if s.split('.')[0].lower() in high_priority_keywords]
        tier1.sort(key=lambda s: s.count('.'))
        
        # Tier 2: remaining quality subdomains
        tier2 = [s for s in quality if s not in tier1]
        tier2.sort(key=lambda s: s.count('.'))
        
        # Build final list
        result = []
        result.extend(tier1[:limit])
        
        remaining = limit - len(result)
        result.extend(tier2[:remaining])
        
        # If still under limit, add back some numeric ones (randomly)
        if len(result) < limit:
            all_subs = [s for s in subdomains_list if s not in result]
            random.shuffle(all_subs)
            result.extend(all_subs[:limit - len(result)])
        
        return result[:limit]

    found_list = list(found)
    if len(found_list) > 150:
        logger.info(f'[{scan_id}] Capping {len(found_list)} found subdomains to 150')
        found_list = prioritize_subdomains(found_list, limit=150)
        
        print(f"Smart cap: {len(found)} → {len(found_list)} subdomains")
        print(f"First 10 selected: {found_list[:10]}")

    # Persist results
    for sub in found_list:
        subdomain = Subdomain(scan_id=scan_id, subdomain=sub)
        db.add(subdomain)
    db.commit()

    logger.info(f'[{scan_id}] Subdomain enumeration complete: {len(found)} subdomains found')
