"""Tenant and Organization models"""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import BaseModel


class Organization(Base, BaseModel):
    """Organization model for multi-tenancy"""

    __tablename__ = "organizations"

    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    tenants = relationship("Tenant", back_populates="organization")
    templates = relationship("Template", back_populates="organization")
    gateways = relationship("Gateway", back_populates="organization")
    deployments = relationship("Deployment", back_populates="organization")
    users = relationship("User", back_populates="organization")
    registration_tokens = relationship("RegistrationToken", back_populates="organization")


class Tenant(Base, BaseModel):
    """Tenant model (sub-organization or workspace)"""

    __tablename__ = "tenants"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="tenants")

