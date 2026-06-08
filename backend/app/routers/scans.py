from fastapi import APIRouter, Depends, HTTPException
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
