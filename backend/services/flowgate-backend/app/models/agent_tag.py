"""Agent Tag model"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import BaseModel


class AgentTag(Base, BaseModel):
    """Agent tag model for tagging gateways"""
    
    __tablename__ = "agent_tags"
    
    gateway_id = Column(UUID(as_uuid=True), ForeignKey("gateways.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(100), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    gateway = relationship("Gateway", backref="agent_tags_list")
    
    __table_args__ = (
        {"comment": "Tags for agents to enable selective config rollouts"}
    )

