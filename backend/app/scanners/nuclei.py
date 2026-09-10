import json
import logging

from app.scanners.utils import normalize_target, run_subprocess

logger = logging.getLogger(__name__)


async def run(targets: list[str]) -> tuple[list[dict], dict]:
    # A target already carrying a scheme is a confirmed-live URL (with the
    # real port) handed down from httpx — keep it as-is rather than
    # normalizing it back down to a bare hostname and losing that port.
    targets = [t if "://" in t else normalize_target(t) for t in targets]
    logger.info(f"Starting nuclei scan for {len(targets)} target(s)")

    command = ["/usr/local/bin/nuclei"]
    for t in targets:
        command += ["-u", t]
    command += [
        "-jsonl", "-silent",
        "-severity", "info,low,medium,high,critical",
        "-tags", "exposure,misconfig,tech",
        "-t", "/root/nuclei-templates",
        # Anti-bot: spoof a real browser so WAF/CDN fingerprinting doesn't block us
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Rate-limit to 50 req/s — avoids 429s from rate-limited targets like github.com
        "-rl", "50",
        # Retry failed requests twice (handles transient 429/reset)
        "-retries", "2",
        # 15s per-template connection timeout (up from 10s default)
        "-timeout", "15",
        # Skip interactsh — no external callbacks, cleaner and faster
        "-no-interactsh",
        # Skip update check at runtime
        "-duc",
    ]
    logger.info(f"nuclei command: {' '.join(command)}")
    findings = []

    stdout, stderr, status = await run_subprocess(command, timeout=600)
    if status["status"] != "success":
        logger.warning(f"nuclei {status['status']}: {status['detail']}")
        return findings, status

    lines = [line for line in stdout.strip().split('\n') if line]
    parse_errors = 0
    for line in lines:
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            parse_errors += 1
            continue

        template_name = data.get("info", {}).get("name", "Unknown")
        matched_at = data.get("matched-at", "")

        findings.append({
            "source": "nuclei",
            "type": "vulnerability",
            "title": f"{template_name}: {matched_at}",
            "raw_data": data,
        })

    if parse_errors:
        logger.warning(f"nuclei: {parse_errors} line(s) failed to parse as JSON")

    if lines and not findings:
        detail = f"could not parse any of {len(lines)} output line(s) as JSON"
        logger.warning(f"nuclei: {detail}")
        return findings, {"status": "failed", "detail": detail}

    logger.info(f"nuclei found {len(findings)} results")
    if not findings:
        logger.warning(f"nuclei returned 0 results. stdout snippet: {stdout[:500]!r}")

    return findings, status
