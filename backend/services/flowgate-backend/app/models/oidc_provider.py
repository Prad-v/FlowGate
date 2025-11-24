"""OIDC Provider model for OAuth/OIDC integration"""

import enum
from sqlalchemy import Column, String, Boolean, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import BaseModel


class OIDCProviderType(str, enum.Enum):
    """OIDC Provider type enum"""
    DIRECT = "direct"  # Direct integration (Okta, Azure AD, Google)
    PROXY = "proxy"  # OAuth proxy integration


class OIDCProvider(Base, BaseModel):
    """OIDC Provider model for OAuth/OIDC authentication"""

    __tablename__ = "oidc_providers"

    name = Column(String(255), nullable=False, unique=True, index=True)
    provider_type = Column(Enum(OIDCProviderType), nullable=False)
    
    # Direct integration fields
    issuer_url = Column(String(500), nullable=True)  # OIDC issuer URL
    client_id = Column(String(255), nullable=True)
    client_secret_encrypted = Column(Text, nullable=True)  # Encrypted client secret
    authorization_endpoint = Column(String(500), nullable=True)
    token_endpoint = Column(String(500), nullable=True)
    userinfo_endpoint = Column(String(500), nullable=True)
    
    # Proxy integration fields
    proxy_url = Column(String(500), nullable=True)  # OAuth proxy URL
    
    # Common fields
    scopes = Column(String(500), nullable=True)  # Comma-separated scopes
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    # org_id is nullable: null means system-wide provider
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)  # Default provider for login page

    # Relationships
    organization = relationship("Organization", back_populates="oidc_providers")
    users = relationship("User", back_populates="oidc_provider")

