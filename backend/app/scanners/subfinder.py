import json
import logging
from .utils import run_cmd

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting subfinder scan for {target}")
    cmd = f"subfinder -d {target} -silent -json"
    code, stdout, stderr = await run_cmd(cmd)
    
    logger.info(f"subfinder stdout length: {len(stdout)}")
    if stderr:
        logger.warning(f"subfinder stderr: {stderr[:500]}")
        
    findings = []
    if code == -1:
        logger.warning(f"Subfinder failed to run or timed out: {stderr}")
        return findings

    for line in stdout.strip().split('\n'):
        if not line:
            continue
        try:
            data = json.loads(line)
            findings.append({
                "source": "subfinder",
                "type": "subdomain",
                "title": f"Subdomain: {data.get('host', '')}",
                "raw_data": data
            })
        except:
            pass
            
    logger.info(f"subfinder found {len(findings)} results for {target}")
    if not findings:
        logger.warning(f"subfinder returned 0 results for {target}. stdout: {stdout[:200]}")
        
    return findings
