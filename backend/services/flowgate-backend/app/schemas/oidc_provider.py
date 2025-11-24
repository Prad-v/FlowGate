"""OIDC provider schemas"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from uuid import UUID
from datetime import datetime


class OIDCProviderCreate(BaseModel):
    """OIDC provider create schema"""
    name: str = Field(..., description="Provider name")
    provider_type: str = Field(..., description="Provider type: 'direct' or 'proxy'")
    
    # Direct integration fields
    issuer_url: Optional[HttpUrl] = Field(None, description="OIDC issuer URL")
    client_id: Optional[str] = Field(None, description="OAuth client ID")
    client_secret: Optional[str] = Field(None, description="OAuth client secret (will be encrypted)")
    authorization_endpoint: Optional[HttpUrl] = Field(None, description="Authorization endpoint URL")
    token_endpoint: Optional[HttpUrl] = Field(None, description="Token endpoint URL")
    userinfo_endpoint: Optional[HttpUrl] = Field(None, description="UserInfo endpoint URL")
    
    # Proxy integration fields
    proxy_url: Optional[HttpUrl] = Field(None, description="OAuth proxy URL")
    
    # Common fields
    scopes: Optional[str] = Field(None, description="Comma-separated OAuth scopes")
    org_id: Optional[UUID] = Field(None, description="Organization ID (null for system-wide)")
    is_active: bool = Field(True, description="Whether provider is active")
    is_default: bool = Field(False, description="Whether this is the default provider")


class OIDCProviderUpdate(BaseModel):
    """OIDC provider update schema"""
    name: Optional[str] = None
    provider_type: Optional[str] = None
    issuer_url: Optional[HttpUrl] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authorization_endpoint: Optional[HttpUrl] = None
    token_endpoint: Optional[HttpUrl] = None
    userinfo_endpoint: Optional[HttpUrl] = None
    proxy_url: Optional[HttpUrl] = None
    scopes: Optional[str] = None
    org_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class OIDCProviderResponse(BaseModel):
    """OIDC provider response schema (without sensitive data)"""
    id: UUID
    name: str
    provider_type: str
    issuer_url: Optional[str] = None
    client_id: Optional[str] = None
    # client_secret is never returned
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    proxy_url: Optional[str] = None
    scopes: Optional[str] = None
    org_id: Optional[UUID] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

