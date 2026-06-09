import json
import logging
import asyncio

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting httpx scan for {target}")
    command = ["/usr/local/bin/httpx", "-u", target, "-json", "-silent", "-tech-detect", "-status-code", "-title", "-web-server"]
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
        
        logger.info(f"httpx stdout length: {len(stdout)}")
        if stderr:
            logger.warning(f"httpx stderr: {stderr[:500]}")
            
        if code == -1 or not stdout:
            logger.warning(f"HTTPX failed to run or timed out: {stderr}")
            return findings
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except:
            pass
        logger.warning("HTTPX timed out")
        return findings
    except Exception as e:
        logger.warning(f"HTTPX failed to execute: {e}")
        return findings

    for line in stdout.strip().split('\n'):
        if not line:
            continue
        try:
            data = json.loads(line)
            findings.append({
                "source": "httpx",
                "type": "technology",
                "title": f"Live Host: {data.get('url', '')}",
                "raw_data": data
            })
        except:
            pass
            
    logger.info(f"httpx found {len(findings)} results for {target}")
    if not findings:
        logger.warning(f"httpx returned 0 results for {target}. stdout: {stdout[:200]}")
        
    return findings
