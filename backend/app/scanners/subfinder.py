import logging
import asyncio

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting subfinder scan for {target}")
    command = ["/usr/local/bin/subfinder", "-d", target, "-silent", "-all"]
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
        
        logger.info(f"subfinder stdout length: {len(stdout)}")
        if stderr:
            logger.warning(f"subfinder stderr (informational): {stderr[:500]}")
            
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except:
            pass
        logger.warning("Subfinder timed out")
        return findings
    except Exception as e:
        logger.warning(f"Subfinder failed to execute: {e}")
        return findings

    if not stdout.strip():
        logger.warning(f"subfinder returned 0 results for {target}.")
        return findings

    for line in stdout.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('['):
            findings.append({
                "source": "subfinder",
                "type": "subdomain",
                "title": f"Subdomain: {line}",
                "raw_data": {"host": line}
            })
            
    logger.info(f"subfinder found {len(findings)} results for {target}")
    return findings
