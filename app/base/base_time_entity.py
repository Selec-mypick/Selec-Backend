from sqlalchemy import Column, DateTime
from app.core.connection_config import Base
from app.core.timezone import now

class BaseTimeEntity(Base):
    __abstract__ = True
    
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)
