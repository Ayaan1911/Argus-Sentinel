import os

subfinder_code = """import json
import logging
import asyncio

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting subfinder scan for {target}")
    command = ["/usr/local/bin/subfinder", "-d", target, "-silent", "-json"]
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
            
        if code == -1 or not stdout:
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
"""

httpx_code = """import json
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

    for line in stdout.strip().split('\\n'):
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
"""

nuclei_code = """import json
import logging
import asyncio

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting nuclei scan for {target}")
    command = ["/usr/local/bin/nuclei", "-u", target, "-json", "-silent", "-severity", "low,medium,high,critical"]
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
        
        logger.info(f"nuclei stdout length: {len(stdout)}")
        if stderr:
            logger.warning(f"nuclei stderr: {stderr[:500]}")
            
        if code == -1 or not stdout:
            logger.warning(f"Nuclei failed to run or timed out: {stderr}")
            return findings
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

nmap_code = """import xml.etree.ElementTree as ET
import logging
import asyncio

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting nmap scan for {target}")
    command = ["/usr/bin/nmap", "-sV", "-sC", "-T4", "--open", "-oX", "-", target]
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
        
        logger.info(f"nmap stdout length: {len(stdout)}")
        if stderr:
            logger.warning(f"nmap stderr: {stderr[:500]}")
            
        if code == -1 or not stdout:
            logger.warning(f"Nmap failed to run or timed out: {stderr}")
            return findings
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except:
            pass
        logger.warning("Nmap timed out")
        return findings
    except Exception as e:
        logger.warning(f"Nmap failed to execute: {e}")
        return findings

    if not stdout:
        return findings

    try:
        root = ET.fromstring(stdout)
        for host in root.findall('host'):
            for port in host.findall('.//port'):
                portid = port.get('portid')
                protocol = port.get('protocol')
                state = port.find('state').get('state') if port.find('state') is not None else ''
                service_el = port.find('service')
                service = service_el.get('name') if service_el is not None else ''
                version = service_el.get('version') if service_el is not None else ''
                
                scripts = {}
                for script in port.findall('script'):
                    scripts[script.get('id')] = script.get('output')
                
                raw_data = {
                    "port": int(portid) if portid else 0,
                    "protocol": protocol,
                    "state": state,
                    "service": service,
                    "version": version,
                    "scripts": scripts
                }
                
                findings.append({
                    "source": "nmap",
                    "type": "port",
                    "title": f"Port {portid}/{protocol}: {service}",
                    "raw_data": raw_data
                })
    except Exception as e:
        logger.warning(f"Failed to parse Nmap XML: {e}")
        
    logger.info(f"nmap found {len(findings)} results for {target}")
    if not findings:
        logger.warning(f"nmap returned 0 results for {target}. stdout: {stdout[:200]}")
        
    return findings
"""

with open("backend/app/scanners/subfinder.py", "w") as f: f.write(subfinder_code)
with open("backend/app/scanners/httpx.py", "w") as f: f.write(httpx_code)
with open("backend/app/scanners/nuclei.py", "w") as f: f.write(nuclei_code)
with open("backend/app/scanners/nmap.py", "w") as f: f.write(nmap_code)

dockerfile_code = """FROM python:3.11-slim

WORKDIR /app

# Install wget, unzip, curl
RUN apt-get update && apt-get install -y wget unzip curl nmap && rm -rf /var/lib/apt/lists/*

# Install subfinder
RUN wget -q https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip -O /tmp/subfinder.zip && \\
    unzip -q /tmp/subfinder.zip subfinder -d /usr/local/bin/ && \\
    chmod +x /usr/local/bin/subfinder && \\
    rm /tmp/subfinder.zip

# Install ProjectDiscovery httpx (NOT pip httpx)
RUN wget -q https://github.com/projectdiscovery/httpx/releases/download/v1.6.5/httpx_1.6.5_linux_amd64.zip -O /tmp/httpx.zip && \\
    unzip -q /tmp/httpx.zip httpx -d /usr/local/bin/ && \\
    chmod +x /usr/local/bin/httpx && \\
    rm /tmp/httpx.zip

# Install nuclei
RUN wget -q https://github.com/projectdiscovery/nuclei/releases/download/v3.2.4/nuclei_3.2.4_linux_amd64.zip -O /tmp/nuclei.zip && \\
    unzip -q /tmp/nuclei.zip nuclei -d /usr/local/bin/ && \\
    chmod +x /usr/local/bin/nuclei && \\
    rm /tmp/nuclei.zip

# Update nuclei templates
RUN nuclei -update-templates -silent || true

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["./start.sh"]
"""
with open("backend/Dockerfile", "w") as f: f.write(dockerfile_code)

with open("backend/requirements.txt", "r") as f:
    lines = f.readlines()
with open("backend/requirements.txt", "w") as f:
    for line in lines:
        if "httpx" not in line.strip():
            f.write(line)
