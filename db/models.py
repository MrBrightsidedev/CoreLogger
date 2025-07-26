from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator, CHAR
import uuid

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses
    CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


class ThoughtModel(Base):
    """SQLAlchemy model for thoughts."""
    
    __tablename__ = "thoughts"

    id = Column(GUID(), primary_key=True, default=uuid4, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    emotion = Column(String(100), nullable=True, index=True)
    importance = Column(Float, nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<ThoughtModel(id={self.id}, category={self.category}, timestamp={self.timestamp})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "category": self.category,
            "content": self.content,
            "tags": self.tags or [],
            "emotion": self.emotion,
            "importance": self.importance,
        }
