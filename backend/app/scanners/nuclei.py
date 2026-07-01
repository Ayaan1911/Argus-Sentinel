import json
import logging
import asyncio

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting nuclei scan for {target}")

    command = [
        "/usr/local/bin/nuclei", "-u", target,
        "-jsonl", "-silent",
        "-severity", "low,medium,high,critical",
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
    findings = []
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=300)
        code = proc.returncode
        stdout = stdout_bytes.decode('utf-8', errors='replace')
        stderr = stderr_bytes.decode('utf-8', errors='replace')

        logger.info(f"nuclei stdout length: {len(stdout)} bytes, returncode: {code}")
        if stderr:
            # Log more stderr so we can see actual 403/429 counts in worker logs
            logger.warning(f"nuclei stderr: {stderr[:2000]}")

    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        logger.warning(f"Nuclei timed out after 300s for {target}")
        return findings
    except Exception as e:
        logger.warning(f"Nuclei failed to execute: {e}")
        return findings

    for line in stdout.strip().split('\n'):
        if not line:
            continue
        try:
            data = json.loads(line)
            template_name = data.get("info", {}).get("name", "Unknown")
            matched_at = data.get("matched-at", "")
            severity = data.get("info", {}).get("severity", "info")
            # Tag WAF-blocked responses so UI can surface them
            status_code = data.get("response", {}) if isinstance(data.get("response"), dict) else {}
            findings.append({
                "source": "nuclei",
                "type": "vulnerability",
                "title": f"{template_name}: {matched_at}",
                "raw_data": data
            })
        except Exception:
            pass

    logger.info(f"nuclei found {len(findings)} results for {target}")
    if not findings:
        logger.warning(f"nuclei returned 0 results for {target}. stdout snippet: {stdout[:500]!r}")

    return findings
