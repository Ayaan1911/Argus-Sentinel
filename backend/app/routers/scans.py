from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.models.scan import Scan
from app.models.finding import Finding
from app.rate_limit import limiter
from app.schemas.scan import ScanCreate, ScanRead
from app.tasks.scan_tasks import run_scan

router = APIRouter()

@router.get("/dashboard-stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Get all findings
    stmt = select(Finding)
    result = await db.execute(stmt)
    findings = result.scalars().all()
    
    # Severity Distribution
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    by_type = {"vulnerability": 0, "port": 0, "subdomain": 0, "technology": 0}
    
    for f in findings:
        sev = f.severity.lower() if f.severity else "info"
        if sev == "informational": sev = "info"
        if sev in by_severity:
            by_severity[sev] += 1
            
        t = f.type.lower() if f.type else "other"
        if t in by_type:
            by_type[t] += 1
        else:
            by_type[t] = 1
            
    # Scans over time (last 14 days)
    fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
    stmt_scans = select(Scan.created_at).where(Scan.created_at >= fourteen_days_ago)
    res_scans = await db.execute(stmt_scans)
    scan_dates = [row[0] for row in res_scans.all()]
    
    scans_by_date = {}
    for i in range(14):
        d = (datetime.utcnow() - timedelta(days=13-i)).strftime("%Y-%m-%d")
        scans_by_date[d] = 0
        
    for d in scan_dates:
        date_str = d.strftime("%Y-%m-%d")
        if date_str in scans_by_date:
            scans_by_date[date_str] += 1
            
    scans_over_time = [{"date": k, "count": v} for k, v in scans_by_date.items()]
    
    return {
        "severity_distribution": by_severity,
        "type_breakdown": by_type,
        "scans_over_time": scans_over_time,
        "total_findings": len(findings)
    }


@router.post("/", response_model=ScanRead)
@limiter.limit("5/minute")
async def create_scan(request: Request, scan_in: ScanCreate, db: AsyncSession = Depends(get_db)):
    # Check for existing scan in progress to prevent duplicates
    stmt = select(Scan).where(Scan.target == scan_in.target, Scan.status.in_(["pending", "running"]))
    result = await db.execute(stmt)
    existing_scan = result.scalars().first()
    
    if existing_scan:
        stmt = select(Scan).options(selectinload(Scan.findings)).where(Scan.id == existing_scan.id)
        res = await db.execute(stmt)
        return res.scalar_one()

    db_scan = Scan(target=scan_in.target, audience=scan_in.audience, status="pending")
    db.add(db_scan)
    await db.commit()
    
    # Trigger celery task
    run_scan.delay(str(db_scan.id), db_scan.target, db_scan.audience)
    
    # Re-fetch with selectinload to prevent Greenlet async load errors during serialization
    stmt = select(Scan).options(selectinload(Scan.findings)).where(Scan.id == db_scan.id)
    result = await db.execute(stmt)
    loaded_scan = result.scalar_one()
    
    return loaded_scan

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
    stmt = select(Scan).options(noload(Scan.findings)).where(Scan.id == scan_id)
    result = await db.execute(stmt)
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    await db.delete(scan)
    await db.commit()
    return {"deleted": True}
