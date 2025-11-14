from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Organization(BaseModel):
    """Organization/Tenant model for multi-tenancy."""
    
    __tablename__ = "organizations"
    
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="organization", cascade="all, delete-orphan")
    gateways = relationship("Gateway", back_populates="organization", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="organization", cascade="all, delete-orphan")

