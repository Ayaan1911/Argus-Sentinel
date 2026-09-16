from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin

class Scan(Base, UUIDMixin):
    __tablename__ = "scans"

    target = Column(String, nullable=False, index=True)
    status = Column(String, default="pending", nullable=False)
    audience = Column(String, default="student", nullable=False)
    # Per-tool status ({"subfinder": {"status": "success", "detail": None}, ...})
    # distinct from the overall `status` column above.
    stage_status = Column(JSONB, nullable=False, default=dict)
    # Set at creation time from settings.DEMO_MODE (see routers/scans.py) —
    # never inferred from the target later. This is what lets the demo-mode
    # pruning task (tasks/scan_tasks.py::prune_demo_scans) delete only scans
    # actually created by the public demo, never a self-hoster's own history
    # even if they happen to scan a target that's also a demo target.
    is_demo = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
