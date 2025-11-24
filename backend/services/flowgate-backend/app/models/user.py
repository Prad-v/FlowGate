"""User model"""

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.base import BaseModel


class User(Base, BaseModel):
    """User model for authentication and authorization"""

    __tablename__ = "users"

    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OIDC-only users
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)  # Nullable for super admin
    # OIDC fields
    oidc_provider_id = Column(UUID(as_uuid=True), ForeignKey("oidc_providers.id"), nullable=True, index=True)
    oidc_subject = Column(String(255), nullable=True, index=True)  # OIDC subject identifier (sub claim)
    # Password management
    password_changed_at = Column(DateTime(timezone=True), nullable=True)  # NULL means must change on first login
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    oidc_provider = relationship("OIDCProvider", back_populates="users")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

