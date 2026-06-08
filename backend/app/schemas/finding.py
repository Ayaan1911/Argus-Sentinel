from pydantic import BaseModel, UUID4
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
    audience_guidance: Optional[Dict[str, str]] = None
    reasoning_breakdown: Optional[List[str]] = None
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
