import json
import logging
import asyncio

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting nuclei scan for {target}")
    command = ["/usr/local/bin/nuclei", "-u", target, "-json", "-silent", "-severity", "low,medium,high,critical"]
    findings = []
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        code = proc.returncode
        stdout = stdout.decode('utf-8', errors='replace')
        stderr = stderr.decode('utf-8', errors='replace')
        
        logger.info(f"nuclei stdout length: {len(stdout)}")
        if stderr:
            logger.warning(f"nuclei stderr: {stderr[:500]}")
            
        if code == -1 or not stdout:
            logger.warning(f"Nuclei failed to run or timed out: {stderr}")
            return findings
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except:
            pass
        logger.warning("Nuclei timed out")
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
            findings.append({
                "source": "nuclei",
                "type": "vulnerability",
                "title": f"{template_name}: {matched_at}",
                "raw_data": data
            })
        except:
            pass
            
    logger.info(f"nuclei found {len(findings)} results for {target}")
    if not findings:
        logger.warning(f"nuclei returned 0 results for {target}. stdout: {stdout[:200]}")
        
    return findings
