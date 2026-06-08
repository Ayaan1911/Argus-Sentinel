import json
import logging
from .utils import run_cmd

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    cmd = f"httpx -u {target} -json -silent -tech-detect -status-code -title -web-server"
    code, stdout, stderr = await run_cmd(cmd)
    
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
    return findings
