from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin

class Finding(Base, UUIDMixin):
    __tablename__ = "findings"

    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    raw_data = Column(JSONB, nullable=True)
    severity = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    technical_impact = Column(Text, nullable=True)
    business_impact = Column(Text, nullable=True)
    attack_patterns = Column(JSONB, nullable=True)
    recommended_actions = Column(JSONB, nullable=True)
    learning_resources = Column(JSONB, nullable=True)
    related_findings = Column(JSONB, nullable=True)
    audience_guidance = Column(JSONB, nullable=True)
    reasoning_breakdown = Column(JSONB, nullable=True)
    correlation_modifier = Column(Float, default=0.0)
    final_risk_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("Scan", back_populates="findings")
