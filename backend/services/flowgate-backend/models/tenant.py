"""Tenant/Organization model."""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel


class Organization(BaseModel):
    """Organization/Tenant model."""
    __tablename__ = "organizations"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(String(1000), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    templates = relationship("Template", back_populates="organization")
    gateways = relationship("Gateway", back_populates="organization")
    deployments = relationship("Deployment", back_populates="organization")


