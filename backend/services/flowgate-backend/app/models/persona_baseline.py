"""Persona Baseline model for Persona Baseline Agent (PBA)"""

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base
from app.models.base import BaseModel


class EntityType(str, enum.Enum):
    """Type of entity for persona baseline"""
    USER = "user"
    SERVICE = "service"
    HOST = "host"


class PersonaBaseline(Base, BaseModel):
    """Behavior baseline for users or services"""

    __tablename__ = "persona_baselines"

    # Entity information
    entity_type = Column(
        SQLEnum(EntityType, name="entity_type", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    entity_id = Column(String(255), nullable=False, index=True)  # User ID, service name, hostname
    entity_name = Column(String(255), nullable=True)

    # Baseline statistics
    baseline_embedding = Column(postgresql.JSONB, nullable=True)  # Vector embedding (stored as JSON for now)
    baseline_stats = Column(postgresql.JSONB, nullable=True)  # Statistical baseline
    behavior_patterns = Column(postgresql.JSONB, nullable=True)  # Common behavior patterns

    # Training information
    training_started_at = Column(DateTime(timezone=True), nullable=True)
    training_completed_at = Column(DateTime(timezone=True), nullable=True)
    sample_count = Column(Integer, default=0, nullable=False)  # Number of samples used
    last_updated_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Anomaly detection
    anomaly_threshold = Column(Float, default=0.7, nullable=False)  # Threshold for anomaly detection
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    organization_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="persona_baselines")
    anomalies = relationship("PersonaAnomaly", back_populates="baseline")


class PersonaAnomaly(Base, BaseModel):
    """Anomaly detected from persona baseline"""

    __tablename__ = "persona_anomalies"

    # Anomaly information
    baseline_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("persona_baselines.id"), nullable=False, index=True)
    deviation_score = Column(Float, nullable=False)  # How much it deviates from baseline
    anomaly_type = Column(String(100), nullable=True)  # e.g., "unusual_time", "unusual_resource", "unusual_pattern"

    # Event that triggered anomaly
    event_data = Column(postgresql.JSONB, nullable=True)  # The event that was anomalous
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Status
    is_investigated = Column(Boolean, default=False, nullable=False)
    investigation_notes = Column(Text, nullable=True)

    # Relationships
    baseline = relationship("PersonaBaseline", back_populates="anomalies")

