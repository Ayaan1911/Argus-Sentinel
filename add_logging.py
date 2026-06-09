import os

subfinder_py = """import json
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

httpx_py = """import json
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

nuclei_py = """import json
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

nmap_py = """import xml.etree.ElementTree as ET
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
"""

scan_tasks_py = """import os
import asyncio
import logging
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.scan import Scan
from app.models.finding import Finding

from app.scanners import subfinder, httpx, nmap, nuclei
from app.scanners.processor import FindingProcessor
from app.engines import correlation_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup sync database for celery
sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
engine = create_engine(sync_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

celery_app = Celery("argus", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

async def _run_scanners(target: str):
    return await asyncio.gather(
        subfinder.run(target),
        httpx.run(target),
        nmap.run(target),
        nuclei.run(target)
    )

@celery_app.task(name="run_scan")
def run_scan(scan_id: str, target: str, audience: str):
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return
            
        scan.status = "running"
        db.commit()
        
        logger.info(f"Running scanners for {target}")
        subfinder_results, httpx_results, nmap_results, nuclei_results = asyncio.run(_run_scanners(target))
        
        logger.info(f"subfinder: {len(subfinder_results)} results")
        logger.info(f"httpx: {len(httpx_results)} results")
        logger.info(f"nmap: {len(nmap_results)} results")
        logger.info(f"nuclei: {len(nuclei_results)} results")
        
        raw_findings = subfinder_results + httpx_results + nmap_results + nuclei_results
        logger.info(f"Total raw findings: {len(raw_findings)}")
        
        processor = FindingProcessor()
        db_findings = []
        
        for raw_f in raw_findings:
            processed = processor.process(raw_f, scan_id, audience)
            db_finding = Finding(**processed)
            db_findings.append(db_finding)
            
        if db_findings:
            db.add_all(db_findings)
            db.flush()
            
            # Convert to dicts for correlation engine
            findings_dicts = []
            for f in db_findings:
                findings_dicts.append({
                    "id": str(f.id),
                    "type": f.type,
                    "title": f.title,
                    "raw_data": f.raw_data,
                    "risk_score": f.risk_score,
                    "severity": f.severity,
                    "reasoning_breakdown": f.reasoning_breakdown,
                    "final_risk_score": f.final_risk_score,
                    "correlation_modifier": f.correlation_modifier
                })
                
            correlation_result = correlation_engine.correlate(findings_dicts)
            updated_dicts = correlation_engine.apply_modifiers(findings_dicts, correlation_result)
            
            # Update DB with final scores
            for ud in updated_dicts:
                f_obj = next((x for x in db_findings if str(x.id) == ud["id"]), None)
                if f_obj:
                    f_obj.final_risk_score = ud["final_risk_score"]
                    f_obj.correlation_modifier = ud["correlation_modifier"]
                    f_obj.reasoning_breakdown = ud["reasoning_breakdown"]
                    
        scan.status = "completed"
        db.commit()
        logger.info(f"Scan {scan_id} completed successfully")
        
    except Exception as e:
        logger.exception(f"Scan {scan_id} failed: {e}")
        db.rollback()
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if scan:
            scan.status = "failed"
            db.commit()
    finally:
        db.close()
"""

with open("backend/app/scanners/subfinder.py", "w") as f:
    f.write(subfinder_py)

with open("backend/app/scanners/httpx.py", "w") as f:
    f.write(httpx_py)

with open("backend/app/scanners/nuclei.py", "w") as f:
    f.write(nuclei_py)

with open("backend/app/scanners/nmap.py", "w") as f:
    f.write(nmap_py)

with open("backend/app/tasks/scan_tasks.py", "w") as f:
    f.write(scan_tasks_py)

print("Updated scanners and tasks")
