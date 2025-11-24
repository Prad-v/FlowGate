"""Incident model for Correlation & RCA Agent (CRA)"""

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base
from app.models.base import BaseModel


class IncidentSeverity(str, enum.Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    """Incident status"""
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(Base, BaseModel):
    """Security incident from Correlation & RCA Agent"""

    __tablename__ = "incidents"

    # Basic information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(
        SQLEnum(IncidentSeverity, name="incident_severity", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    status = Column(
        SQLEnum(IncidentStatus, name="incident_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=IncidentStatus.NEW,
        index=True
    )

    # Timeline
    detected_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)  # When attack started
    contained_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Root cause analysis
    root_cause = Column(Text, nullable=True)
    root_cause_confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    attack_path = Column(postgresql.JSONB, nullable=True)  # Attack path graph
    blast_radius = Column(postgresql.JSONB, nullable=True)  # Affected entities

    # Correlated data
    correlated_alerts = Column(postgresql.ARRAY(postgresql.UUID), nullable=True)  # Threat alert IDs
    correlated_logs = Column(postgresql.JSONB, nullable=True)  # Key log entries
    timeline = Column(postgresql.JSONB, nullable=True)  # Event timeline

    # Investigation
    assigned_to = Column(String(255), nullable=True)  # Analyst user ID
    investigation_notes = Column(Text, nullable=True)
    evidence_bundle = Column(postgresql.JSONB, nullable=True)  # Evidence collection

    # Relationships
    organization_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="incidents")
    threat_alerts = relationship("ThreatAlert", back_populates="incident")

