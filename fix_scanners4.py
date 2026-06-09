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

    for line in stdout.strip().split('\\n'):
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
"""

# Update nuclei.py
nuclei_code = """import json
import logging
import asyncio

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting nuclei scan for {target}")
    
    # Check version first
    try:
        ver_proc = await asyncio.create_subprocess_exec(
            "/usr/local/bin/nuclei", "-version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        ver_out, ver_err = await asyncio.wait_for(ver_proc.communicate(), timeout=30)
        logger.info(f"nuclei version stdout: {ver_out.decode('utf-8', errors='replace').strip()}")
        logger.info(f"nuclei version stderr: {ver_err.decode('utf-8', errors='replace').strip()}")
    except Exception as e:
        logger.warning(f"Failed to check nuclei version: {e}")

    command = [
        "/usr/local/bin/nuclei", "-u", target, "-json", "-silent",
        "-severity", "low,medium,high,critical",
        "-tags", "exposure,misconfig,tech",
        "-timeout", "30", "-duc", "-no-interactsh"
    ]
    findings = []
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=120)
        code = proc.returncode
        stdout = stdout_bytes.decode('utf-8', errors='replace')
        stderr = stderr_bytes.decode('utf-8', errors='replace')
        
        logger.info(f"nuclei stdout length: {len(stdout)}")
        if stderr:
            logger.warning(f"nuclei stderr: {stderr[:500]}")
            
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

    for line in stdout.strip().split('\\n'):
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
"""

with open("backend/app/scanners/subfinder.py", "w") as f:
    f.write(subfinder_code)

with open("backend/app/scanners/nuclei.py", "w") as f:
    f.write(nuclei_code)

with open("backend/Dockerfile", "r") as f:
    content = f.read()

content = content.replace(
    "RUN nuclei -update-templates -silent || true",
    "RUN /usr/local/bin/nuclei -update-templates -duc -silent || true"
)

with open("backend/Dockerfile", "w") as f:
    f.write(content)

print("Updated scanners and Dockerfile")
