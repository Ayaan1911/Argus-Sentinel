import json
import logging

from app.intelligence.loader import get_intelligence_loader
from app.scanners.utils import is_outdated, normalize_target, run_subprocess

logger = logging.getLogger(__name__)

ADMIN_PATH_PATTERNS = ("/admin", "/login", "wp-admin", "phpmyadmin", "/dashboard", "/manage")
ADMIN_TITLE_KEYWORDS = ("admin", "login", "dashboard", "phpmyadmin", "control panel")


def _detect_admin_panel(data: dict) -> bool:
    url = str(data.get("url", "")).lower()
    title = str(data.get("title", "")).lower()
    if any(p in url for p in ADMIN_PATH_PATTERNS):
        return True
    if any(k in title for k in ADMIN_TITLE_KEYWORDS):
        return True
    return False


def _detect_known_vulnerabilities(tech_list: list) -> bool:
    if not tech_list:
        return False
    # httpx's -tech-detect sometimes reports "Nginx:1.18.0" — match on the
    # name only, not the embedded version.
    detected = {str(t).split(":")[0].strip().lower() for t in tech_list}
    loader = get_intelligence_loader()
    for entry in loader.data.get("vulnerabilities", {}).values():
        affected = {t.lower() for t in entry.get("affected_technologies", [])}
        if affected & detected:
            return True
    return False


def _detect_outdated_tech(tech_list: list) -> bool:
    """Checks each detected tech's own embedded version (e.g. "jQuery:3.4.1")
    against that technology's min_secure_version on file, if any. This is the
    client-side-library equivalent of nmap.py's server-product version check
    — same "min_secure_version" field, different detection source."""
    if not tech_list:
        return False
    loader = get_intelligence_loader()
    for t in tech_list:
        parts = str(t).split(":", 1)
        if len(parts) != 2:
            continue
        name, version = parts[0].strip().lower(), parts[1].strip()
        entry = loader.data.get("technologies", {}).get(name)
        if not entry:
            continue
        if is_outdated(version, entry.get("min_secure_version")):
            return True
    return False


# Web apps commonly run on these non-standard ports too (juice-shop's default
# is 3000). httpx's own "-ports" flag is broken in the pinned v1.6.5 binary
# (it mis-parses bare hostnames into a malformed URL), so the candidate
# host:port URLs are built here instead and fed to httpx directly via stdin.
EXTRA_PORTS = (3000, 8000, 8080, 8888)


async def run(targets: list[str]) -> tuple[list[dict], dict]:
    targets = [normalize_target(t) for t in targets]
    logger.info(f"Starting httpx scan for {len(targets)} target(s)")
    probe_urls = []
    for t in targets:
        probe_urls += [f"http://{t}", f"https://{t}"]
        probe_urls += [f"http://{t}:{p}" for p in EXTRA_PORTS]
    command = [
        "/usr/local/bin/httpx",
        "-json",
        "-silent",
        "-title",
        "-web-server",
        "-tech-detect",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "-retries", "2",
        "-timeout", "10",
        "-follow-redirects",
        "-mc", "200,201,301,302,303,307,308,401,403,404,500,502,503",
    ]
    findings = []

    stdin_payload = ("\n".join(probe_urls)).encode("utf-8")
    stdout, stderr, status = await run_subprocess(command, timeout=300, input_bytes=stdin_payload)
    if status["status"] != "success":
        logger.warning(f"httpx {status['status']}: {status['detail']}")
        return findings, status

    lines = [line for line in stdout.strip().split('\n') if line]
    parse_errors = 0
    for line in lines:
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            parse_errors += 1
            continue

        status_code = data.get("status_code", 0)
        waf_note = ""
        if status_code in [401, 403, 503]:
            waf_note = " (WAF/CDN protected - may require further evasion)"
            data["waf_detected"] = True

        tech_list = data.get("tech", []) or []
        data["admin_panel_exposed"] = _detect_admin_panel(data)
        data["known_vulnerabilities"] = _detect_known_vulnerabilities(tech_list)
        data["outdated_version"] = _detect_outdated_tech(tech_list)

        findings.append({
            "source": "httpx",
            "type": "technology",
            "title": f"Live Host: {data.get('url', '')}{waf_note}",
            "raw_data": data,
        })

    if parse_errors:
        logger.warning(f"httpx: {parse_errors} line(s) failed to parse as JSON")

    # Every line was output but none of it was usable JSON — that's a distinct
    # failure from "ran fine, found nothing" (empty stdout).
    if lines and not findings:
        detail = f"could not parse any of {len(lines)} output line(s) as JSON"
        logger.warning(f"httpx: {detail}")
        return findings, {"status": "failed", "detail": detail}

    logger.info(f"httpx found {len(findings)} results")
    if not findings:
        logger.warning(f"httpx returned 0 results. stdout: {stdout[:200]}")

    return findings, status
