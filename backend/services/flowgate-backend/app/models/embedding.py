"""Embedding model for vector storage"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base
from app.models.base import BaseModel


class EmbeddingType(str, enum.Enum):
    """Type of embedding"""
    LOG_PATTERN = "log_pattern"
    TTP_PATTERN = "ttp_pattern"
    BEHAVIOR_PATTERN = "behavior_pattern"
    USER_BEHAVIOR = "user_behavior"
    SERVICE_BEHAVIOR = "service_behavior"


class Embedding(Base, BaseModel):
    """Vector embedding for similarity search"""

    __tablename__ = "embeddings"

    # Embedding information
    embedding_type = Column(
        SQLEnum(EmbeddingType, name="embedding_type", create_type=False),
        nullable=False,
        index=True
    )
    entity_id = Column(String(255), nullable=True, index=True)  # Related entity ID
    entity_type = Column(String(100), nullable=True)  # Related entity type

    # Vector data (stored as JSONB for now, can be migrated to pgvector later)
    # Note: pgvector requires special column type, we'll add migration for that
    vector_data = Column(postgresql.JSONB, nullable=False)  # Array of floats
    vector_dimension = Column(Integer, nullable=False)  # Dimension of vector

    # Metadata
    source_data = Column(postgresql.JSONB, nullable=True)  # Original data that was embedded
    metadata_ = Column(postgresql.JSONB, nullable=True)  # Additional metadata (using _ to avoid SQLAlchemy reserved name)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    organization_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="embeddings")

