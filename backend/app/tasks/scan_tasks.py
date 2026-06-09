import os
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
