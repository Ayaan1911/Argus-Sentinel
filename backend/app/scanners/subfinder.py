import logging
import random
import string

import dns.exception
import dns.resolver

from app.scanners.utils import is_internal_ip, run_subprocess

logger = logging.getLogger(__name__)

# CNAME suffixes for third-party services commonly abandoned, making the
# subdomain pointing at them a subdomain-takeover candidate if the target
# itself no longer resolves.
TAKEOVER_CNAME_FINGERPRINTS = (
    "github.io",
    "herokuapp.com",
    "s3.amazonaws.com",
    "cloudfront.net",
    "azurewebsites.net",
    "trafficmanager.net",
)


def _resolve_a(hostname: str) -> str | None:
    try:
        answers = dns.resolver.resolve(hostname, "A", lifetime=5)
        return str(answers[0])
    except (dns.exception.DNSException, Exception):
        return None


def _resolve_cname(hostname: str) -> str | None:
    try:
        answers = dns.resolver.resolve(hostname, "CNAME", lifetime=5)
        return str(answers[0].target).rstrip(".")
    except (dns.exception.DNSException, Exception):
        return None


def _is_wildcard_domain(domain: str) -> bool:
    probe_label = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    return _resolve_a(f"{probe_label}.{domain}") is not None


def _is_takeover_candidate(hostname: str) -> bool:
    cname = _resolve_cname(hostname)
    if not cname:
        return False
    if not any(fp in cname.lower() for fp in TAKEOVER_CNAME_FINGERPRINTS):
        return False
    # Heuristic only: CNAME points at a known third-party host but that host
    # itself doesn't resolve -> likely dangling/unclaimed. Not a verified
    # takeover, just a candidate worth a human looking at.
    return _resolve_a(cname) is None


async def run(target: str) -> tuple[list[dict], dict]:
    logger.info(f"Starting subfinder scan for {target}")
    command = ["/usr/local/bin/subfinder", "-d", target, "-silent", "-all"]

    stdout, stderr, status = await run_subprocess(command, timeout=300)
    if status["status"] != "success":
        logger.warning(f"subfinder {status['status']} for {target}: {status['detail']}")
        return [], status

    hosts = [
        line.strip() for line in stdout.strip().split('\n')
        if line.strip() and not line.strip().startswith('[')
    ]

    if not hosts:
        logger.info(f"subfinder found 0 results for {target}")
        return [], status

    wildcard = _is_wildcard_domain(target)
    if wildcard:
        logger.warning(f"{target} appears to have wildcard DNS — subdomain results may be unreliable")

    findings = []
    for host in hosts:
        raw_data = {"host": host, "wildcard_subdomain": wildcard}

        resolved_ip = _resolve_a(host)
        if resolved_ip is not None:
            raw_data["resolved_ip"] = resolved_ip
            raw_data["resolves_to_internal_ip"] = is_internal_ip(resolved_ip)

        raw_data["takeover_possible"] = _is_takeover_candidate(host)

        findings.append({
            "source": "subfinder",
            "type": "subdomain",
            "title": f"Subdomain: {host}",
            "raw_data": raw_data,
        })

    logger.info(f"subfinder found {len(findings)} results for {target}")
    return findings, status
