import logging
import requests
from app.models import Subdomain, TakeoverRisk

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 8

# FINGERPRINTS: provider -> (cname_keyword, response_body_fingerprint)
# cname_keyword: string that should appear in the CNAME target for this provider
# response_body_fingerprint: string that indicates the subdomain is dangling / claimable
FINGERPRINTS: dict[str, tuple[str, str]] = {
    'GitHub Pages':       ('github.io',          "There isn't a GitHub Pages site here"),
    'Heroku':             ('herokudns.com',       'No such app'),
    'Heroku (Alt)':       ('herokuapp.com',       'No such app'),
    'AWS S3':             ('s3.amazonaws.com',    'NoSuchBucket'),
    'AWS CloudFront':     ('cloudfront.net',      'The request could not be satisfied'),
    'AWS Elastic Beanstalk': ('elasticbeanstalk.com', 'Error 404'),
    'Netlify':            ('netlify.app',         'Not Found - Request ID'),
    'Netlify (Alt)':      ('netlify.com',         'Not Found'),
    'Azure Web App':      ('azurewebsites.net',   '404 Web Site not Found'),
    'Azure CDN':          ('azureedge.net',       'The resource you are looking for'),
    'Azure Traffic Mgr':  ('trafficmanager.net',  'Page not found'),
    'Ghost':              ('ghost.io',            "The thing you were looking for is no longer here"),
    'Cargo':              ('cargocollective.com', '404 Not Found'),
    'Tumblr':             ('tumblr.com',          "There's nothing here."),
    'WordPress.com':      ('wordpress.com',       'Do you want to register'),
    'Pantheon':           ('pantheonsite.io',     '404 error unknown site'),
    'Fastly':             ('fastly.net',          'Fastly error: unknown domain'),
    'Shopify':            ('myshopify.com',       'Sorry, this shop is currently unavailable'),
    'Squarespace':        ('squarespace.com',     'No Such Account'),
    'Zendesk':            ('zendesk.com',         'Help Center Closed'),
    'Readme.io':          ('readme.io',           "Project doesn't exist"),
    'Surge.sh':           ('surge.sh',            'project not found'),
    'Webflow':            ('webflow.io',          "The page you are looking for doesn't exist"),
    'Fly.io':             ('fly.dev',             "fly.io"),
    'Vercel':             ('vercel.app',          'The deployment could not be found'),
    'Render':             ('onrender.com',        'No such app'),
    'Strikingly':         ('strikingly.com',      'page not found'),
    'Unbounce':           ('unbouncepages.com',   'The requested URL was not found'),
    'HubSpot':            ('hubspot.net',         'Domain not found'),
    'Intercom':           ('intercom.help',       'Page Not Found'),
    'LaunchRock':         ('launchrock.com',      'It looks like you may have taken a wrong turn somewhere'),
    'Tilda':              ('tilda.cc',            'Please renew your subscription'),
    'Pingdom':            ('pingdom.net',         'Public Report Not Activated'),
    'Statuspage.io':      ('statuspage.io',       'You are being redirected'),
}


def _get_cname(hostname: str) -> str | None:
    """Resolve CNAME record for a hostname using dnspython."""
    try:
        import dns.resolver
        answers = dns.resolver.resolve(hostname, 'CNAME')
        return str(answers[0].target).rstrip('.')
    except Exception:
        return None


def _check_fingerprint(hostname: str, fingerprint: str) -> bool:
    """Fetch hostname over HTTP and check if fingerprint appears in response."""
    for scheme in ('http', 'https'):
        try:
            resp = requests.get(
                f'{scheme}://{hostname}',
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            if fingerprint.lower() in resp.text.lower():
                return True
        except requests.RequestException:
            continue
    return False


def run(scan_id: str, db) -> None:
    """
    Stage 7: Subdomain Takeover Check.
    For each subdomain:
    1. Resolve CNAME record
    2. Check if CNAME matches a known vulnerable provider
    3. Confirm vulnerability by fetching the page and checking for the fingerprint string
    Stores confirmed risks in the takeover_risks table.
    """
    try:
        import dns.resolver
        has_dns = True
    except ImportError:
        logger.warning('[takeover_check] dnspython not available — CNAME resolution disabled')
        has_dns = False

    subdomains = db.query(Subdomain).filter(Subdomain.scan_id == scan_id).all()
    if not subdomains:
        logger.info(f'[{scan_id}] No subdomains for takeover check')
        return

    logger.info(f'[{scan_id}] Checking {len(subdomains)} subdomains for takeover risks')
    print(f"[STAGE] takeover_check: input={len(subdomains)} subdomains")
    count = 0

    for sub in subdomains:
        cname_target = _get_cname(sub.subdomain) if has_dns else None

        for provider, (cname_keyword, fingerprint) in FINGERPRINTS.items():
            # Determine if CNAME matches this provider's keyword
            cname_matches = cname_target and cname_keyword.lower() in cname_target.lower()

            # Only proceed if we have a CNAME match (or no DNS to check)
            if not cname_matches and has_dns:
                continue

            # Confirm with HTTP fingerprint check
            if _check_fingerprint(sub.subdomain, fingerprint):
                risk = TakeoverRisk(
                    scan_id=scan_id,
                    subdomain=sub.subdomain,
                    cname=cname_target,
                    provider=provider,
                    fingerprint=fingerprint,
                )
                db.add(risk)
                count += 1
                logger.warning(
                    f'[{scan_id}] TAKEOVER RISK: {sub.subdomain} -> '
                    f'{cname_target} ({provider})'
                )
                break  # One risk per subdomain is enough

    db.commit()
    
    total_takeovers = db.query(TakeoverRisk).filter(TakeoverRisk.scan_id == scan_id).count()
    print(f"[STAGE] takeover_check: output={total_takeovers} takeovers")
    print(f"[DB] Verified {total_takeovers} takeovers committed for scan {scan_id}")
    
    logger.info(f'[{scan_id}] Takeover check complete: {count} risk(s) found')
