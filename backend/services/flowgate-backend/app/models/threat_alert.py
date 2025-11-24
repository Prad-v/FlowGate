"""Threat Alert model for Threat Vector Agent (TVA)"""

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base
from app.models.base import BaseModel


class ThreatSeverity(str, enum.Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatStatus(str, enum.Enum):
    """Threat alert status"""
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class ThreatAlert(Base, BaseModel):
    """Threat alert from Threat Vector Agent"""

    __tablename__ = "threat_alerts"

    # Basic information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(
        SQLEnum(ThreatSeverity, name="threat_severity", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    status = Column(
        SQLEnum(ThreatStatus, name="threat_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ThreatStatus.NEW,
        index=True
    )

    # MITRE ATT&CK mapping
    mitre_technique_id = Column(String(50), nullable=True)  # e.g., "T1055"
    mitre_technique_name = Column(String(255), nullable=True)
    mitre_tactic = Column(String(100), nullable=True)  # e.g., "Execution", "Persistence"
    mitre_tactics = Column(postgresql.ARRAY(String), nullable=True)  # Multiple tactics

    # Source information
    source_type = Column(String(100), nullable=False, index=True)  # identity, network, endpoint, application
    source_entity = Column(String(255), nullable=True)  # User ID, IP, hostname, etc.
    source_log_id = Column(String(255), nullable=True)  # Reference to original log

    # Detection details
    confidence_score = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    anomaly_score = Column(Float, nullable=True)  # Anomaly detection score
    detection_method = Column(String(100), nullable=True)  # rule_based, ml_based, embedding_match

    # Context and metadata
    raw_log_data = Column(postgresql.JSONB, nullable=True)  # Original log entry
    enriched_data = Column(postgresql.JSONB, nullable=True)  # Enriched with context
    indicators = Column(postgresql.JSONB, nullable=True)  # IOCs, IPs, domains, etc.

    # Timestamps
    detected_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    first_seen = Column(DateTime(timezone=True), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    incident_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="threat_alerts")
    incident = relationship("Incident", back_populates="threat_alerts")

