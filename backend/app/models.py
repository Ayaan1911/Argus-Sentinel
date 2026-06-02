import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Scan(Base):
    __tablename__ = 'scans'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    domain = Column(String, nullable=False)
    status = Column(String, default='queued')  # queued/running/complete/failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    current_stage = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    subdomains = relationship('Subdomain', back_populates='scan', cascade='all, delete-orphan')
    secrets = relationship('Secret', back_populates='scan', cascade='all, delete-orphan')
    endpoints = relationship('Endpoint', back_populates='scan', cascade='all, delete-orphan')
    takeover_risks = relationship('TakeoverRisk', back_populates='scan', cascade='all, delete-orphan')
    ai_summary = relationship('AISummary', back_populates='scan', uselist=False, cascade='all, delete-orphan')
    vulnerability_findings = relationship('VulnerabilityFinding', back_populates='scan', cascade='all, delete-orphan')


class Subdomain(Base):
    __tablename__ = 'subdomains'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, ForeignKey('scans.id'), nullable=False, index=True)
    subdomain = Column(String, nullable=False)
    is_alive = Column(Boolean, default=False)
    status_code = Column(Integer, nullable=True)
    title = Column(String, nullable=True)
    technologies = Column(JSON, default=list)
    screenshot_path = Column(String, nullable=True)

    scan = relationship('Scan', back_populates='subdomains')
    ports = relationship('Port', back_populates='subdomain', cascade='all, delete-orphan')


class Port(Base):
    __tablename__ = 'ports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    subdomain_id = Column(Integer, ForeignKey('subdomains.id'), nullable=False, index=True)
    port = Column(Integer, nullable=False)
    protocol = Column(String, default='tcp')
    service = Column(String, nullable=True)
    version = Column(String, nullable=True)

    subdomain = relationship('Subdomain', back_populates='ports')


class Secret(Base):
    __tablename__ = 'secrets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, ForeignKey('scans.id'), nullable=False, index=True)
    file_url = Column(String, nullable=False)
    secret_type = Column(String, nullable=False)
    matched_value = Column(String, nullable=False)
    line_number = Column(Integer, nullable=True)
    severity = Column(String, nullable=True, default='medium')
    confidence = Column(Integer, nullable=True, default=60)
    
    validated = Column(Boolean, default=False)
    validation_proof = Column(Text, nullable=True)

    scan = relationship('Scan', back_populates='secrets')


class Endpoint(Base):
    __tablename__ = 'endpoints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, ForeignKey('scans.id'), nullable=False, index=True)
    url = Column(String, nullable=False)
    source_file = Column(String, nullable=True)

    scan = relationship('Scan', back_populates='endpoints')


class TakeoverRisk(Base):
    __tablename__ = 'takeover_risks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, ForeignKey('scans.id'), nullable=False, index=True)
    subdomain = Column(String, nullable=False)
    cname = Column(String, nullable=True)
    provider = Column(String, nullable=False)
    fingerprint = Column(String, nullable=True)

    scan = relationship('Scan', back_populates='takeover_risks')


class AISummary(Base):
    __tablename__ = 'ai_summaries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, ForeignKey('scans.id'), nullable=False, unique=True, index=True)
    summary_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship('Scan', back_populates='ai_summary')


class VulnerabilityFinding(Base):
    __tablename__ = 'vulnerability_findings'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey('scans.id'), nullable=False, index=True)
    template_id = Column(String, nullable=False)
    template_name = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # critical, high, medium, low, info
    host = Column(String, nullable=False)
    matched_at = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship('Scan', back_populates='vulnerability_findings')
