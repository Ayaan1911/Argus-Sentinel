import os

files = {
    "backend/app/models/base.py": """import uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
""",
    "backend/app/models/scan.py": """from sqlalchemy import Column, String, DateTime
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
""",
    "backend/app/models/finding.py": """from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime
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
""",
    "backend/app/models/__init__.py": """from .base import Base
from .scan import Scan
from .finding import Finding
""",
    "backend/app/schemas/finding.py": """from pydantic import BaseModel, UUID4
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
""",
    "backend/app/schemas/scan.py": """from pydantic import BaseModel, UUID4
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
""",
    "backend/app/schemas/__init__.py": """from .scan import ScanCreate, ScanRead, ScanStatusUpdate
from .finding import FindingCreate, FindingRead
""",
    "backend/app/database.py": """from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.base import Base

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
""",
    "backend/app/main.py": """from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Argus Sentinel API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")
app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Argus Sentinel"}
""",
    "backend/alembic/env.py": """import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os

from app.models.base import Base
import app.models  # ensure models are imported

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
}

for filepath, content in files.items():
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("DB Layer building complete.")
