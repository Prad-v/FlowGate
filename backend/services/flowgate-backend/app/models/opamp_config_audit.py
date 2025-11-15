"""OpAMP Config Audit model"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
import enum
from app.database import Base
from app.models.base import BaseModel


class OpAMPConfigAuditStatus(str, enum.Enum):
    """OpAMP config audit status enumeration"""
    
    PENDING = "pending"
    APPLYING = "applying"
    APPLIED = "applied"
    FAILED = "failed"


class OpAMPConfigAudit(Base, BaseModel):
    """OpAMP config audit model for tracking config updates"""
    
    __tablename__ = "opamp_config_audit"
    
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("opamp_config_deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    gateway_id = Column(UUID(as_uuid=True), ForeignKey("gateways.id", ondelete="CASCADE"), nullable=False, index=True)
    config_version = Column(Integer, nullable=False, index=True)
    config_hash = Column(String(256), nullable=False)
    status = Column(
        ENUM('pending', 'applying', 'applied', 'failed', 
             name='opamp_config_audit_status', create_type=False),
        nullable=False
    )
    status_reported_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    effective_config_hash = Column(String(256), nullable=True)  # From agent
    
    # Relationships
    deployment = relationship("OpAMPConfigDeployment", back_populates="audit_entries")
    gateway = relationship("Gateway", backref="config_audit_entries")
    
    __table_args__ = (
        {"comment": "Audit log for OpAMP config deployments per agent"}
    )

