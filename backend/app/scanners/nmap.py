import xml.etree.ElementTree as ET
import logging
import asyncio

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    logger.info(f"Starting nmap scan for {target}")
    findings = []
    try:
        proc = await asyncio.create_subprocess_exec(
            "nmap", "-sV", "-sC", "-T4", "--open", "-oX", "-", target,
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
