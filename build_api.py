import os

files = {
    "backend/app/routers/__init__.py": "",
    "backend/app/routers/scans.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any

from app.database import get_db
from app.models.scan import Scan
from app.schemas.scan import ScanCreate, ScanRead
from app.tasks.scan_tasks import run_scan

router = APIRouter()

@router.post("/", response_model=ScanRead)
async def create_scan(scan_in: ScanCreate, db: AsyncSession = Depends(get_db)):
    db_scan = Scan(target=scan_in.target, audience=scan_in.audience, status="pending")
    db.add(db_scan)
    await db.commit()
    await db.refresh(db_scan)
    
    # Trigger celery task
    run_scan.delay(str(db_scan.id), db_scan.target, db_scan.audience)
    
    return db_scan

@router.get("/", response_model=List[Dict[str, Any]])
async def list_scans(db: AsyncSession = Depends(get_db)):
    stmt = select(Scan).options(selectinload(Scan.findings)).order_by(Scan.created_at.desc())
    result = await db.execute(stmt)
    scans = result.scalars().all()
    
    out = []
    for s in scans:
        out.append({
            "id": str(s.id),
            "target": s.target,
            "status": s.status,
            "audience": s.audience,
            "created_at": s.created_at,
            "finding_count": len(s.findings)
        })
    return out

@router.get("/{scan_id}", response_model=ScanRead)
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Scan).options(selectinload(Scan.findings)).where(Scan.id == scan_id)
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@router.get("/{scan_id}/status")
async def get_scan_status(scan_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Scan).options(selectinload(Scan.findings)).where(Scan.id == scan_id)
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {
        "scan_id": str(scan.id),
        "status": scan.status,
        "finding_count": len(scan.findings)
    }

@router.delete("/{scan_id}")
async def delete_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Scan).where(Scan.id == scan_id)
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    await db.delete(scan)
    await db.commit()
    return {"deleted": True}
""",
    "backend/app/routers/findings.py": """from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models.scan import Scan
from app.models.finding import Finding
from app.schemas.finding import FindingRead

router = APIRouter()

def _get_risk_level(score: float) -> str:
    if score <= 2.0: return "informational"
    if score <= 4.0: return "low"
    if score <= 6.0: return "medium"
    if score <= 8.0: return "high"
    return "critical"

@router.get("/scan/{scan_id}", response_model=List[FindingRead])
async def get_scan_findings(
    scan_id: str,
    severity: Optional[str] = None,
    type: Optional[str] = None,
    min_risk: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Finding).where(Finding.scan_id == scan_id)
    
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if type:
        stmt = stmt.where(Finding.type == type)
    if min_risk is not None:
        stmt = stmt.where(Finding.final_risk_score >= min_risk)
        
    stmt = stmt.order_by(Finding.final_risk_score.desc())
    
    result = await db.execute(stmt)
    findings = result.scalars().all()
    return findings

@router.get("/{finding_id}", response_model=FindingRead)
async def get_finding(finding_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Finding).where(Finding.id == finding_id)
    result = await db.execute(stmt)
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding

@router.get("/scan/{scan_id}/summary")
async def get_scan_summary(scan_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Scan).options(selectinload(Scan.findings)).where(Scan.id == scan_id)
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
        
    findings = scan.findings
    
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
    by_type = {"port": 0, "subdomain": 0, "vulnerability": 0, "technology": 0, "service": 0}
    
    max_risk = 0.0
    for f in findings:
        sev = f.severity.lower() if f.severity else "informational"
        if sev in by_severity:
            by_severity[sev] += 1
            
        t = f.type.lower() if f.type else ""
        if t in by_type:
            by_type[t] += 1
        elif t:
            by_type[t] = 1
            
        if f.final_risk_score > max_risk:
            max_risk = f.final_risk_score

    # Determine top findings
    sorted_findings = sorted(findings, key=lambda x: x.final_risk_score, reverse=True)
    top_findings = []
    for f in sorted_findings[:5]:
        top_findings.append({
            "id": str(f.id),
            "type": f.type,
            "title": f.title,
            "severity": f.severity,
            "final_risk_score": f.final_risk_score
        })
        
    combined_risk_modifier = 0.0
    high_sev_count = sum(1 for f in findings if f.risk_score >= 6.1)
    if high_sev_count >= 3:
        combined_risk_modifier += 1.5
    combined_risk = max_risk + combined_risk_modifier
    combined_risk = max(0.0, min(10.0, combined_risk))
    
    return {
        "scan_id": str(scan.id),
        "target": scan.target,
        "total_findings": len(findings),
        "by_severity": by_severity,
        "by_type": by_type,
        "top_findings": top_findings,
        "combined_risk_level": _get_risk_level(combined_risk),
        "audience": scan.audience
    }
""",
    "backend/app/routers/intelligence.py": """from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from app.intelligence.loader import get_intelligence_loader

router = APIRouter()

@router.get("/services")
async def list_services():
    loader = get_intelligence_loader()
    return loader._cache.get("services", {})

@router.get("/services/{name}")
async def get_service(name: str):
    loader = get_intelligence_loader()
    entry = loader.get_service(name)
    if not entry:
        raise HTTPException(status_code=404, detail="Service not found")
    return entry

@router.get("/technologies")
async def list_technologies():
    loader = get_intelligence_loader()
    return loader._cache.get("technologies", {})

@router.get("/technologies/{name}")
async def get_technology(name: str):
    loader = get_intelligence_loader()
    entry = loader.get_technology(name)
    if not entry:
        raise HTTPException(status_code=404, detail="Technology not found")
    return entry

@router.get("/vulnerabilities")
async def list_vulnerabilities():
    loader = get_intelligence_loader()
    return loader._cache.get("vulnerabilities", {})

@router.get("/vulnerabilities/{name}")
async def get_vulnerability(name: str):
    loader = get_intelligence_loader()
    entry = loader.get_vulnerability(name)
    if not entry:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return entry

@router.get("/search")
async def search_intelligence(q: str = Query(..., min_length=1)):
    loader = get_intelligence_loader()
    results = []
    query = q.lower()
    
    for category in ["services", "technologies", "vulnerabilities"]:
        items = loader._cache.get(category, {})
        for name, data in items.items():
            if query in name.lower() or query in str(data.get("description", "")).lower() or query in str(data.get("service", "")).lower() or query in str(data.get("technology", "")).lower():
                results.append({
                    "type": category.rstrip("ies").rstrip("s") if category != "technologies" else "technology",
                    "entry": data
                })
    return results
""",
    "backend/app/main.py": """import time
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from redis.asyncio import Redis

from app.config import settings
from app.database import init_db, get_db
from app.tasks import celery_app

from app.routers import scans, findings, intelligence
from app.intelligence.loader import get_intelligence_loader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Initialize intelligence loader cache
    get_intelligence_loader()
    yield

app = FastAPI(
    title="Argus Sentinel API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} "
        f"status_code={response.status_code} "
        f"response_time_ms={process_time_ms:.2f}"
    )
    return response

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": str(exc.detail)}
    )

from fastapi.exceptions import RequestValidationError
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An unexpected error occurred"}
    )

app.include_router(scans.router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(findings.router, prefix="/api/v1/findings", tags=["findings"])
app.include_router(intelligence.router, prefix="/api/v1/intelligence", tags=["intelligence"])

@app.get("/health")
async def health_check():
    # Check DB
    db_status = "disconnected"
    try:
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"DB health check failed: {e}")

    # Check Redis
    redis_status = "disconnected"
    try:
        r = Redis.from_url(settings.REDIS_URL)
        await r.ping()
        redis_status = "connected"
        await r.close()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

    # Intelligence info
    loader = get_intelligence_loader()
    
    return {
        "status": "ok",
        "service": "Argus Sentinel",
        "version": "1.0.0",
        "database": db_status,
        "redis": redis_status,
        "intelligence_library": {
            "services": len(loader._cache.get("services", {})),
            "technologies": len(loader._cache.get("technologies", {})),
            "vulnerabilities": len(loader._cache.get("vulnerabilities", {}))
        }
    }
"""
}

for filepath, content in files.items():
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("API Layer building complete.")
