"""Deployment model."""
from sqlalchemy import Column, String, ForeignKey, JSON, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Deployment(BaseModel):
    """Deployment/Rollout model."""
    __tablename__ = "deployments"
    
    name = Column(String(255), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=False)
    template_version = Column(Integer, nullable=False)
    gateway_id = Column(UUID(as_uuid=True), ForeignKey("gateways.id"), nullable=True)  # null = all gateways
    status = Column(String(50), default="pending", nullable=False)  # 'pending', 'in_progress', 'completed', 'failed', 'rolled_back'
    rollout_strategy = Column(String(50), default="immediate", nullable=False)  # 'immediate', 'canary', 'staged'
    canary_percentage = Column(Integer, nullable=True)  # For canary rollouts
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String(1000), nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional deployment metadata
    
    # Relationships
    organization = relationship("Organization", back_populates="deployments")
    gateway = relationship("Gateway", back_populates="deployments")
