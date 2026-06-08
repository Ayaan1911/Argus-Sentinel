from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin

class Scan(Base, UUIDMixin):
    __tablename__ = "scans"

    target = Column(String, nullable=False, index=True)
    status = Column(String, default="pending", nullable=False)
    audience = Column(String, default="student", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
