import os

# Update subfinder.py
subfinder_code = """import logging
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
            logger.warning(f"subfinder stderr: {stderr[:500]}")
            
        if code != 0 and not stdout.strip():
            logger.warning(f"Subfinder failed to run or timed out: {stderr}")
            return findings
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

    for line in stdout.strip().split('\\n'):
        line = line.strip()
        if not line:
            continue
        
        findings.append({
            "source": "subfinder",
            "type": "subdomain",
            "title": f"Subdomain: {line}",
            "raw_data": {"host": line}
        })
            
    logger.info(f"subfinder found {len(findings)} results for {target}")
    if not findings:
        logger.warning(f"subfinder returned 0 results for {target}. stdout: {stdout[:200]}")
        
    return findings
"""
with open("backend/app/scanners/subfinder.py", "w") as f:
    f.write(subfinder_code)

# Update Dockerfile
with open("backend/Dockerfile", "r") as f:
    content = f.read()

content = content.replace(
    "https://github.com/projectdiscovery/nuclei/releases/download/v3.2.4/nuclei_3.2.4_linux_amd64.zip",
    "https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_linux_amd64.zip"
).replace(
    "unzip -q /tmp/nuclei.zip nuclei -d /usr/local/bin/",
    "unzip -q /tmp/nuclei.zip nuclei -d /usr/local/bin/"
)

with open("backend/Dockerfile", "w") as f:
    f.write(content)

print("Updated subfinder and Dockerfile")
