from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class PortSchema(BaseModel):
    id: int
    port: int
    protocol: str
    service: Optional[str] = None
    version: Optional[str] = None

    class Config:
        from_attributes = True

class PortDetailSchema(BaseModel):
    id: int
    port: int
    protocol: str
    service: Optional[str] = None
    version: Optional[str] = None
    subdomain: str

    class Config:
        from_attributes = True


class SubdomainSchema(BaseModel):
    id: int
    subdomain: str
    is_alive: bool
    status_code: Optional[int] = None
    title: Optional[str] = None
    technologies: Optional[List[str]] = []
    ports: List[PortSchema] = []
    screenshot_path: Optional[str] = None

    class Config:
        from_attributes = True


class SecretSchema(BaseModel):
    id: int
    file_url: str
    secret_type: str
    matched_value: str
    line_number: Optional[int] = None
    severity: Optional[str] = 'medium'
    confidence: Optional[int] = 60
    
    validated: Optional[bool] = False
    validation_proof: Optional[str] = None

    class Config:
        from_attributes = True


class EndpointSchema(BaseModel):
    id: int
    url: str
    source_file: Optional[str] = None

    class Config:
        from_attributes = True


class TakeoverRiskSchema(BaseModel):
    id: int
    subdomain: str
    cname: Optional[str] = None
    provider: str
    fingerprint: Optional[str] = None

    class Config:
        from_attributes = True


class AISummarySchema(BaseModel):
    id: int
    summary_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class VulnerabilityFindingSchema(BaseModel):
    id: str
    template_id: str
    template_name: str
    severity: str
    host: str
    matched_at: str
    description: Optional[str] = None
    remediation: Optional[str] = None
    tags: Optional[List[str]] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ScanSchema(BaseModel):
    id: str
    domain: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    subdomains: List[SubdomainSchema] = []
    secrets: List[SecretSchema] = []
    endpoints: List[EndpointSchema] = []
    takeover_risks: List[TakeoverRiskSchema] = []
    ai_summary: Optional[AISummarySchema] = None
    vulnerability_findings: List[VulnerabilityFindingSchema] = []
    
    ports: List[PortDetailSchema] = []
    
    subdomains_count: Optional[int] = 0
    live_hosts_count: Optional[int] = 0
    ports_count: Optional[int] = 0
    screenshots_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ScanListSchema(BaseModel):
    id: str
    domain: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    current_stage: Optional[str] = None
    subdomain_count: int = 0

    class Config:
        from_attributes = True


def envelope(data=None, success: bool = True, error: Optional[str] = None) -> dict:
    """Standard API response envelope."""
    return {"success": success, "data": data, "error": error}
