import re
import logging
from app.models import Secret
from .js_extractor import get_js_cache

logger = logging.getLogger(__name__)

# Maximum matched value length stored in DB (truncated for safety)
MAX_STORED_LENGTH = 60

# Severity classification by secret type (normalized key)
SECRET_SEVERITY_MAP: dict[str, str] = {
    'aws access key id':          'critical',
    'aws secret access key':      'critical',
    'github token':               'critical',
    'private key':                'critical',
    'stripe secret key':          'high',
    'github personal access token': 'high',
    'github oauth token':         'high',
    'slack bot/user token':       'high',
    'slack webhook url':          'high',
    'hardcoded password':         'high',
    'bearer token':               'high',
    'api key':                    'high',
    'sendgrid api key':           'high',
    'jwt token':                  'medium',
    'generic api key':            'medium',
    'generic secret':             'medium',
    'google api key':             'medium',
    'twilio account sid':         'medium',
    'twilio auth token':          'medium',
    'database connection string': 'medium',
    'mailgun api key':            'medium',
    'npm auth token':             'medium',
    'mailchimp api key':          'low',
    'stripe publishable key':     'low',
    'google oauth client id':     'low',
    'firebase url':               'info',
}

# Confidence score (0–100) per secret type
SECRET_CONFIDENCE_MAP: dict[str, int] = {
    'aws access key id':            95,
    'aws secret access key':        95,
    'github token':                 95,
    'api key':                      85,
    'private key':                  99,
    'stripe secret key':            92,
    'github personal access token': 90,
    'github oauth token':           90,
    'slack bot/user token':         88,
    'slack webhook url':            90,
    'hardcoded password':           75,
    'bearer token':                 80,
    'sendgrid api key':             90,
    'jwt token':                    75,
    'generic api key':              60,
    'generic secret':               55,
    'google api key':               80,
    'twilio account sid':           85,
    'twilio auth token':            82,
    'database connection string':   85,
    'mailgun api key':              85,
    'npm auth token':               80,
    'mailchimp api key':            85,
    'stripe publishable key':       90,
    'google oauth client id':       70,
    'firebase url':                 80,
}


def _classify_secret(secret_type: str) -> tuple[str, int]:
    """
    Return (severity, confidence) for a given secret type label.
    Normalizes the key and performs fuzzy fallback matching.
    """
    key = secret_type.lower().strip()

    # Exact match
    if key in SECRET_SEVERITY_MAP:
        return SECRET_SEVERITY_MAP[key], SECRET_CONFIDENCE_MAP.get(key, 60)

    # Partial match
    for k, sev in SECRET_SEVERITY_MAP.items():
        if k in key or key in k:
            conf = SECRET_CONFIDENCE_MAP.get(k, 60)
            return sev, conf

    # Keyword fallback
    if any(word in key for word in ('private', 'rsa', 'pem', 'certificate')):
        return 'critical', 95
    if any(word in key for word in ('aws', 'secret', 'password', 'passwd', 'token', 'github', 'slack', 'stripe')):
        return 'high', 70
    if any(word in key for word in ('api', 'key', 'jwt', 'oauth', 'database', 'db', 'connection')):
        return 'medium', 60
    if any(word in key for word in ('publishable', 'public', 'firebase', 'url')):
        return 'low', 55

    return 'info', 50


# Each pattern: (secret_type_label, compiled_regex)
# Patterns use capturing groups where the secret value is in group 1,
# or no group (full match is used).
PATTERNS: list[tuple[str, re.Pattern]] = [
    # Cloud provider keys
    ('AWS Access Key ID',
     re.compile(r'\b(AKIA[0-9A-Z]{16})\b')),

    ('AWS Secret Access Key',
     re.compile(r'(?:aws[_\-\.]?secret[_\-\.]?(?:access[_\-\.]?)?key)\s*[=:]\s*[\'"]?\s*([A-Za-z0-9/+=]{40})\b', re.IGNORECASE)),

    ('Google API Key',
     re.compile(r'\b(AIza[0-9A-Za-z\-_]{35})\b')),

    ('Google OAuth Client ID',
     re.compile(r'\b([0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com)\b')),

    ('Firebase URL',
     re.compile(r'https?://([a-z0-9-]+\.firebaseio\.com)', re.IGNORECASE)),

    # Auth tokens
    ('JWT Token',
     re.compile(r'\b(eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,})\b')),

    ('Bearer Token',
     re.compile(r'Bearer ([a-zA-Z0-9\-._~+/]+=*)', re.IGNORECASE)),

    # Private keys / certificates
    ('Private Key',
     re.compile(r'(-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)', re.IGNORECASE)),

    # SaaS / platform tokens
    ('Slack Bot/User Token',
     re.compile(r'\b(xox[baprs]-[0-9A-Za-z\-]{10,})\b')),

    ('Slack Webhook URL',
     re.compile(r'(https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+)')),

    ('GitHub Token',
     re.compile(r'\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})\b')),

    ('Stripe Secret Key',
     re.compile(r'\b(sk_live_[0-9a-zA-Z]{24,})\b')),

    ('Stripe Publishable Key',
     re.compile(r'\b(pk_live_[0-9a-zA-Z]{24,})\b')),

    ('SendGrid API Key',
     re.compile(r'\b(SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43})\b')),

    ('Twilio Account SID',
     re.compile(r'\b(AC[a-zA-Z0-9]{32})\b')),

    ('Twilio Auth Token',
     re.compile(r'\b(SK[0-9a-fA-F]{32})\b')),

    ('Mailgun API Key',
     re.compile(r'\b(key-[0-9a-zA-Z]{32})\b')),

    ('Mailchimp API Key',
     re.compile(r'\b([0-9a-f]{32}-us[0-9]{1,2})\b')),

    ('NPM Auth Token',
     re.compile(r'(?://registry\.npmjs\.org/:_authToken=)([a-zA-Z0-9\-_]{36})', re.IGNORECASE)),

    # Generic secrets
    ('API Key',
     re.compile(r'(?:api_key|apikey|api-key|access_key|secret_key)\s*[=:]\s*[\'"]?([a-zA-Z0-9_-]{32,45})\b', re.IGNORECASE)),

    ('Generic Secret',
     re.compile(r'(?:secret|secret[_\-\.]?key|client[_\-\.]?secret)\s*[=:]\s*[\'"]?([a-zA-Z0-9\-_+/]{16,})', re.IGNORECASE)),

    ('Hardcoded Password',
     re.compile(r'(?:password|passwd|pwd)\s*[=:]\s*[\'"](?=[a-zA-Z]*[^a-zA-Z\'"])([^\s\'"]{8,})[\'"]', re.IGNORECASE)),

    ('Database Connection String',
     re.compile(r'(?:mongodb|postgresql|mysql|redis|amqp|jdbc)://[^\s\'"<>]{10,}', re.IGNORECASE)),
]


def _extract_value(pattern: re.Pattern, line: str) -> str | None:
    """
    Extract the most relevant value from a regex match.
    Uses group(1) if the pattern has a capturing group, otherwise group(0).
    """
    m = pattern.search(line)
    if not m:
        return None
    try:
        return m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0)
    except IndexError:
        return m.group(0)


def run(scan_id: str, db) -> None:
    """
    Stage 5: Secret Detection.
    Scans all cached JS file content line-by-line using regex patterns.
    Stores matches with type, source file, line number, truncated value,
    severity, and confidence score.
    """
    js_files = get_js_cache(scan_id)
    if not js_files:
        logger.info(f'[{scan_id}] No JS files in cache, skipping secret detection')
        return

    print(f"[STAGE] secret_detector: input={len(js_files)} JS files")
    count = 0
    seen: set[str] = set()  # Deduplicate exact same match per file

    for file_url, content in js_files.items():
        lines = content.splitlines()
        for line_no, line in enumerate(lines, start=1):
            # Skip blank lines
            if not line.strip():
                continue

            for secret_type, pattern in PATTERNS:
                value = _extract_value(pattern, line)
                if not value:
                    continue

                # Deduplicate: same type + value + file
                dedup_key = f'{file_url}:{secret_type}:{value}'
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                stored_value = value[:MAX_STORED_LENGTH]
                severity, confidence = _classify_secret(secret_type)
                
                # Confidence filter > 0.7 (70 out of 100)
                if confidence <= 70:
                    continue

                secret = Secret(
                    scan_id=scan_id,
                    file_url=file_url,
                    secret_type=secret_type,
                    matched_value=stored_value,
                    line_number=line_no,
                    severity=severity,
                    confidence=confidence,
                )
                db.add(secret)
                count += 1

    db.commit()
    
    total_secrets = db.query(Secret).filter(Secret.scan_id == scan_id).count()
    print(f"[STAGE] secret_detector: output={total_secrets} secrets")
    print(f"[DB] Verified {total_secrets} secrets committed for scan {scan_id}")
    
    logger.info(f'[{scan_id}] Secret detection complete: {count} secret(s) found')
