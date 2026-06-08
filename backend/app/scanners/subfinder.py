import json
import logging
from .utils import run_cmd

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    cmd = f"subfinder -d {target} -silent -json"
    code, stdout, stderr = await run_cmd(cmd)
    
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
    return findings
