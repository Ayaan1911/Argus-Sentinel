import os

files = {
    "backend/app/scanners/__init__.py": "",
    "backend/app/scanners/utils.py": """import asyncio
import re

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\\x1B(?:[@-Z\\\\-_]|\\\\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

async def run_cmd(cmd: str, timeout: int = 300):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, strip_ansi(stdout.decode('utf-8', errors='replace')), strip_ansi(stderr.decode('utf-8', errors='replace'))
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except:
            pass
        return -1, "", "Timeout exceeded"
    except Exception as e:
        return -1, "", str(e)
""",
    "backend/app/scanners/subfinder.py": """import json
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
    return findings
""",
    "backend/app/scanners/httpx.py": """import json
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
    return findings
""",
    "backend/app/scanners/nmap.py": """import xml.etree.ElementTree as ET
import logging
from .utils import run_cmd

logger = logging.getLogger(__name__)

async def run(target: str) -> list[dict]:
    cmd = f"nmap -sV -sC -T4 --open -oX - {target}"
    code, stdout, stderr = await run_cmd(cmd)
    
    findings = []
    if code == -1:
        logger.warning(f"Nmap failed to run or timed out: {stderr}")
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
        
    return findings
""",
    "backend/app/scanners/nuclei.py": """import json
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
    return findings
""",
    "backend/app/scanners/processor.py": """from app.intelligence.loader import get_intelligence_loader
from app.engines import reasoning_engine, confidence_engine

class FindingProcessor:
    def __init__(self):
        self.loader = get_intelligence_loader()

    def process(self, raw_finding: dict, scan_id: str, audience: str) -> dict:
        f_type = raw_finding.get("type", "").lower()
        title = raw_finding.get("title", "")
        raw_data = raw_finding.get("raw_data", {})
        source = raw_finding.get("source", "unknown")

        kb_entry = None
        if f_type in ["port", "service"]:
            service_name = raw_data.get("service", "")
            kb_entry = self.loader.get_service(service_name)
        elif f_type == "technology":
            tech_name = raw_data.get("title", "") # fallback or actual detection
            kb_entry = self.loader.get_technology(tech_name)
        elif f_type == "vulnerability":
            vuln_name = raw_data.get("info", {}).get("name", "")
            kb_entry = self.loader.get_vulnerability(vuln_name)
        
        if kb_entry is None:
            kb_entry = {}

        reasoning_res = reasoning_engine.calculate_risk(f_type, raw_data, kb_entry)
        confidence_res = confidence_engine.calculate_confidence(source, raw_data, kb_entry)

        risk_level = reasoning_res.risk_level
        
        if risk_level in ["critical", "high"]:
            biz_impact = "Significant business risk"
        elif risk_level == "medium":
            biz_impact = "Moderate business risk"
        else:
            biz_impact = "Minimal business risk"

        audience_data = kb_entry.get("audience_guidance", {})
        guidance = {audience: audience_data.get(audience, "")} if audience_data else {}

        return {
            "scan_id": scan_id,
            "type": f_type,
            "title": title,
            "raw_data": raw_data,
            "severity": risk_level,
            "confidence": confidence_res.final_confidence,
            "risk_score": reasoning_res.total_score,
            "technical_impact": kb_entry.get("description", "Unknown"),
            "business_impact": biz_impact,
            "audience_guidance": guidance,
            "recommended_actions": kb_entry.get("recommended_actions", []),
            "learning_resources": kb_entry.get("learning_resources", []),
            "reasoning_breakdown": reasoning_res.reasoning_breakdown,
            "attack_patterns": kb_entry.get("attack_patterns", []),
            "related_findings": kb_entry.get("related_findings", []),
            "correlation_modifier": 0.0,
            "final_risk_score": reasoning_res.total_score
        }
""",
    "backend/app/tasks/__init__.py": """from .scan_tasks import celery_app
""",
    "backend/app/tasks/scan_tasks.py": """import os
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
        scanner_results = asyncio.run(_run_scanners(target))
        raw_findings = [f for res in scanner_results for f in res]
        
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
}

# Update main.py to import tasks
main_py_path = "backend/app/main.py"
with open(main_py_path, 'r') as f:
    main_py_content = f.read()

if "from app.tasks import celery_app" not in main_py_content:
    main_py_content = "from app.tasks import celery_app\\n" + main_py_content
    with open(main_py_path, 'w') as f:
        f.write(main_py_content)

for filepath, content in files.items():
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Scanners and tasks building complete.")
