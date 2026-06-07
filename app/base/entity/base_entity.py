from sqlalchemy import Column, DateTime, String
from app.core.database import Base
from app.core.utils import now


class BaseTimeEntity(Base):
    __abstract__ = True

    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)


class BaseAuditEntity(BaseTimeEntity):
    __abstract__ = True

    created_by = Column(String(36), nullable=False)
    updated_by = Column(String(36), nullable=False)
