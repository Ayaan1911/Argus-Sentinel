import re
import logging
from app.models import Secret
from .js_extractor import get_js_cache

logger = logging.getLogger(__name__)

# Maximum matched value length stored in DB (truncated for safety)
MAX_STORED_LENGTH = 60

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
     re.compile(r'[Aa]uthorization\s*[=:]\s*[\'"]?[Bb]earer\s+([a-zA-Z0-9\-._~+/]+=*)', re.IGNORECASE)),

    # Private keys / certificates
    ('Private Key (PEM)',
     re.compile(r'(-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----)', re.IGNORECASE)),

    # SaaS / platform tokens
    ('Slack Bot/User Token',
     re.compile(r'\b(xox[baprs]-[0-9A-Za-z\-]{10,})\b')),

    ('Slack Webhook URL',
     re.compile(r'(https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+)')),

    ('GitHub Personal Access Token',
     re.compile(r'\b(gh[pousr]_[A-Za-z0-9]{36})\b')),

    ('GitHub OAuth Token',
     re.compile(r'\b(gho_[A-Za-z0-9]{36})\b')),

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
    ('Generic API Key',
     re.compile(r'(?:api[_\-\.]?key|apikey|api_token)\s*[=:]\s*[\'"]?([a-zA-Z0-9\-_]{20,})', re.IGNORECASE)),

    ('Generic Secret',
     re.compile(r'(?:secret|secret[_\-\.]?key|client[_\-\.]?secret)\s*[=:]\s*[\'"]?([a-zA-Z0-9\-_+/]{16,})', re.IGNORECASE)),

    ('Hardcoded Password',
     re.compile(r'(?:password|passwd|pwd)\s*[=:]\s*[\'"]([^\s\'"]{8,})[\'"]', re.IGNORECASE)),

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
    Stores matches with type, source file, line number, and truncated value.
    """
    js_files = get_js_cache(scan_id)
    if not js_files:
        logger.info(f'[{scan_id}] No JS files in cache, skipping secret detection')
        return

    count = 0
    seen: set[str] = set()  # Deduplicate exact same match per file

    for file_url, content in js_files.items():
        lines = content.splitlines()
        for line_no, line in enumerate(lines, start=1):
            # Skip blank lines and minified megaliths (>5000 chars per line, scan anyway)
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

                secret = Secret(
                    scan_id=scan_id,
                    file_url=file_url,
                    secret_type=secret_type,
                    matched_value=stored_value,
                    line_number=line_no,
                )
                db.add(secret)
                count += 1

    db.commit()
    logger.info(f'[{scan_id}] Secret detection complete: {count} potential secret(s) found')
