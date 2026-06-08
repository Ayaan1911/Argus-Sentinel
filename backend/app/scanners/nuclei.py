import json
import logging
from .utils import run_cmd

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    cmd = f"nuclei -u {target} -json -silent -severity low,medium,high,critical"
    code, stdout, stderr = await run_cmd(cmd)
    
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
    return findings
