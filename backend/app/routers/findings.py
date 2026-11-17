from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from typing import List, Optional

from app.database import get_db
from app.config import settings
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
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Finding).where(Finding.scan_id == scan_id)
    if settings.DEMO_MODE:
        stmt = stmt.join(Scan).where(Scan.is_demo.is_(True))

    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if type:
        stmt = stmt.where(Finding.type == type)
    if min_risk is not None:
        stmt = stmt.where(Finding.final_risk_score >= min_risk)

    stmt = stmt.order_by(Finding.final_risk_score.desc(), Finding.id.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    findings = result.scalars().all()
    return findings

@router.get("/{finding_id}", response_model=FindingRead)
async def get_finding(finding_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Finding).where(Finding.id == finding_id)
    if settings.DEMO_MODE:
        stmt = stmt.join(Scan).where(Scan.is_demo.is_(True))
    result = await db.execute(stmt)
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding

@router.get("/scan/{scan_id}/summary")
async def get_scan_summary(scan_id: str, db: AsyncSession = Depends(get_db)):
    # Query scan separately
    stmt_scan = select(Scan).where(Scan.id == scan_id)
    if settings.DEMO_MODE:
        stmt_scan = stmt_scan.where(Scan.is_demo.is_(True))
    result_scan = await db.execute(stmt_scan)
    scan = result_scan.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
        
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
    by_type = {"port": 0, "subdomain": 0, "vulnerability": 0, "technology": 0, "service": 0}

    severity_stmt = (select(Finding.severity, func.count(Finding.id))
                     .where(Finding.scan_id == scan_id).group_by(Finding.severity))
    for severity, count in (await db.execute(severity_stmt)).all():
        key = (severity or "informational").lower()
        if key == "info":
            key = "informational"
        if key in by_severity:
            by_severity[key] += count

    type_stmt = (select(Finding.type, func.count(Finding.id))
                 .where(Finding.scan_id == scan_id).group_by(Finding.type))
    for type_, count in (await db.execute(type_stmt)).all():
        key = (type_ or "").lower()
        if key:
            by_type[key] = by_type.get(key, 0) + count

    aggregate_stmt = select(
        func.count(Finding.id), func.max(Finding.final_risk_score),
        func.sum(case((Finding.risk_score >= 6.1, 1), else_=0)),
    ).where(Finding.scan_id == scan_id)
    total, max_risk, high_sev_count = (await db.execute(aggregate_stmt)).one()
    top_stmt = (select(Finding).where(Finding.scan_id == scan_id)
                .order_by(Finding.final_risk_score.desc(), Finding.id.desc()).limit(5))
    top_findings = [
        {"id": str(f.id), "type": f.type, "title": f.title,
         "severity": f.severity, "final_risk_score": f.final_risk_score}
        for f in (await db.execute(top_stmt)).scalars().all()
    ]
    combined_risk = min(10.0, (max_risk or 0.0) + (1.5 if (high_sev_count or 0) >= 3 else 0.0))

    return {
        "scan_id": str(scan.id),
        "target": scan.target,
        "total_findings": total,
        "by_severity": by_severity,
        "by_type": by_type,
        "top_findings": top_findings,
        "combined_risk_level": _get_risk_level(combined_risk),
        "audience": scan.audience
    }
