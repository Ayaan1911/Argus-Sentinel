import os

# findings.py
findings_content = """from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
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
    # Query scan separately
    stmt_scan = select(Scan).where(Scan.id == scan_id)
    result_scan = await db.execute(stmt_scan)
    scan = result_scan.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
        
    # Query findings directly
    stmt_findings = select(Finding).where(Finding.scan_id == scan_id)
    result_findings = await db.execute(stmt_findings)
    findings = result_findings.scalars().all()
    
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
"""
with open("backend/app/routers/findings.py", "w") as f:
    f.write(findings_content)


# finding.py schema
schema_content = """from pydantic import BaseModel, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime

class FindingBase(BaseModel):
    type: str
    title: str
    raw_data: Optional[Dict[str, Any]] = None
    severity: str
    confidence: float
    risk_score: float
    technical_impact: Optional[str] = None
    business_impact: Optional[str] = None
    attack_patterns: Optional[List[str]] = None
    recommended_actions: Optional[List[str]] = None
    learning_resources: Optional[List[str]] = None
    related_findings: Optional[List[str]] = None
    audience_guidance: Optional[Dict[str, Any]] = None
    reasoning_breakdown: Optional[List[Dict[str, Any]]] = None
    correlation_modifier: float = 0.0
    final_risk_score: float

class FindingCreate(FindingBase):
    pass

class FindingRead(FindingBase):
    id: UUID4
    scan_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True
"""
with open("backend/app/schemas/finding.py", "w") as f:
    f.write(schema_content)
