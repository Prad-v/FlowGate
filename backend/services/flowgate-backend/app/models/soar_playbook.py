"""SOAR Playbook model for SOAR Automation Agent (SAA)"""

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base
from app.models.base import BaseModel


class PlaybookStatus(str, enum.Enum):
    """Playbook execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlaybookTriggerType(str, enum.Enum):
    """Type of trigger for playbook"""
    THREAT_ALERT = "threat_alert"
    INCIDENT = "incident"
    ACCESS_REQUEST = "access_request"
    ANOMALY = "anomaly"
    MANUAL = "manual"


class SOARPlaybook(Base, BaseModel):
    """SOAR playbook definition"""

    __tablename__ = "soar_playbooks"

    # Playbook information
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False, default="1.0.0")

    # Playbook definition
    playbook_yaml = Column(Text, nullable=False)  # YAML definition of playbook
    trigger_type = Column(
        SQLEnum(PlaybookTriggerType, name="playbook_trigger_type", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    trigger_conditions = Column(postgresql.JSONB, nullable=True)  # Conditions for auto-trigger

    # Configuration
    is_enabled = Column(Boolean, default=True, nullable=False, index=True)
    requires_approval = Column(Boolean, default=False, nullable=False)
    risk_threshold = Column(Float, nullable=True)  # Minimum risk score to auto-trigger

    # Relationships
    organization_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="soar_playbooks")
    executions = relationship("PlaybookExecution", back_populates="playbook")


class PlaybookExecution(Base, BaseModel):
    """SOAR playbook execution record"""

    __tablename__ = "playbook_executions"

    # Execution information
    playbook_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("soar_playbooks.id"), nullable=False, index=True)
    status = Column(
        SQLEnum(PlaybookStatus, name="playbook_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PlaybookStatus.PENDING,
        index=True
    )

    # Trigger information
    trigger_type = Column(
        SQLEnum(PlaybookTriggerType, name="playbook_trigger_type", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    trigger_entity_id = Column(String(255), nullable=True)  # ID of triggering entity (alert, incident, etc.)
    trigger_entity_type = Column(String(100), nullable=True)

    # Execution details
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_logs = Column(postgresql.JSONB, nullable=True)  # Step-by-step execution logs
    actions_taken = Column(postgresql.JSONB, nullable=True)  # Actions executed
    errors = Column(postgresql.ARRAY(Text), nullable=True)  # Any errors encountered

    # Approval (if required)
    approved_by = Column(String(255), nullable=True)  # User ID
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="playbook_executions")
    playbook = relationship("SOARPlaybook", back_populates="executions")

