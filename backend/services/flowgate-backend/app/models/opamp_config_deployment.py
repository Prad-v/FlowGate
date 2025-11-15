"""OpAMP Config Deployment model"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship
import enum
from app.database import Base
from app.models.base import BaseModel


class OpAMPConfigDeploymentStatus(str, enum.Enum):
    """OpAMP config deployment status enumeration"""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class OpAMPConfigDeployment(Base, BaseModel):
    """OpAMP config deployment model"""
    
    __tablename__ = "opamp_config_deployments"
    
    name = Column(String(255), nullable=False)
    config_version = Column(Integer, nullable=False, unique=True, index=True)  # Global version
    config_yaml = Column(Text, nullable=False)
    config_hash = Column(String(256), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=True)
    template_version = Column(Integer, nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    rollout_strategy = Column(String(50), nullable=False, default="immediate")
    canary_percentage = Column(Integer, nullable=True)
    target_tags = Column(JSONB, nullable=True)  # Array of tag names
    status = Column(
        ENUM('pending', 'in_progress', 'completed', 'failed', 'rolled_back', 
             name='opamp_config_deployment_status', create_type=False),
        nullable=False,
        default=OpAMPConfigDeploymentStatus.PENDING
    )
    ignore_failures = Column(Boolean, nullable=False, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    organization = relationship("Organization", backref="opamp_config_deployments")
    template = relationship("Template")
    audit_entries = relationship("OpAMPConfigAudit", back_populates="deployment", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"comment": "OpAMP config deployments with global versioning"}
    )

