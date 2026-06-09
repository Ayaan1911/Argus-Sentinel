import json
import logging
from .utils import run_cmd

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting httpx scan for {target}")
    cmd = f"httpx -u {target} -json -silent -tech-detect -status-code -title -web-server"
    code, stdout, stderr = await run_cmd(cmd)
    
    logger.info(f"httpx stdout length: {len(stdout)}")
    if stderr:
        logger.warning(f"httpx stderr: {stderr[:500]}")
        
    findings = []
    if code == -1:
        logger.warning(f"HTTPX failed to run or timed out: {stderr}")
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
