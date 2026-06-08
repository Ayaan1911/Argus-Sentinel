import uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
