from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime
from .finding import FindingRead

class ScanBase(BaseModel):
    target: str
    audience: str = "student"

class ScanCreate(ScanBase):
    pass

class ScanStatusUpdate(BaseModel):
    status: str

class ScanRead(ScanBase):
    id: UUID4
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    findings: List[FindingRead] = []

    class Config:
        from_attributes = True
