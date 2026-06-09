import json
import logging
from .utils import run_cmd

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting nuclei scan for {target}")
    cmd = f"nuclei -u {target} -json -silent -severity low,medium,high,critical"
    code, stdout, stderr = await run_cmd(cmd)
    
    logger.info(f"nuclei stdout length: {len(stdout)}")
    if stderr:
        logger.warning(f"nuclei stderr: {stderr[:500]}")
        
    findings = []
    if code == -1:
        logger.warning(f"Nuclei failed to run or timed out: {stderr}")
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
