"""Deployment model"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.database import Base
from app.models.base import BaseModel


class DeploymentStatus(str, enum.Enum):
    """Deployment status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class RolloutStrategy(str, enum.Enum):
    """Rollout strategy enumeration"""

    IMMEDIATE = "immediate"
    CANARY = "canary"
    STAGED = "staged"


class Deployment(Base, BaseModel):
    """Deployment model for template rollouts"""

    __tablename__ = "deployments"

    name = Column(String(255), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=False, index=True)
    template_version = Column(Integer, nullable=False)
    gateway_id = Column(UUID(as_uuid=True), ForeignKey("gateways.id"), nullable=True, index=True)  # None = all gateways
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    status = Column(SQLEnum(DeploymentStatus), default=DeploymentStatus.PENDING, nullable=False)
    rollout_strategy = Column(SQLEnum(RolloutStrategy), default=RolloutStrategy.IMMEDIATE, nullable=False)
    canary_percentage = Column(Integer, default=0)  # For canary rollouts
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    extra_metadata = Column(JSONB)  # Additional deployment metadata

    # Relationships
    organization = relationship("Organization", back_populates="deployments")
    template = relationship("Template")
    gateway = relationship("Gateway", back_populates="deployments")

