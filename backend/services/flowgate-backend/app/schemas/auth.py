"""Authentication schemas"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime

if TYPE_CHECKING:
    from app.schemas.auth import UserResponse


class LoginRequest(BaseModel):
    """Login request schema"""
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Password")
    org_id: Optional[UUID] = Field(None, description="Organization ID (for super admin)")


class UserResponse(BaseModel):
    """User response schema"""
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    org_id: Optional[UUID]
    oidc_provider_id: Optional[UUID]
    password_changed_at: Optional[datetime]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    requires_password_change: bool = False


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    old_password: Optional[str] = Field(None, description="Current password (required if not first login)")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


class UserResponse(BaseModel):
    """User response schema"""
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    org_id: Optional[UUID]
    oidc_provider_id: Optional[UUID]
    password_changed_at: Optional[datetime]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class OIDCProviderResponse(BaseModel):
    """OIDC provider response schema"""
    id: UUID
    name: str
    provider_type: str
    is_active: bool
    is_default: bool
    org_id: Optional[UUID]

    class Config:
        from_attributes = True


class OIDCAuthorizeRequest(BaseModel):
    """OIDC authorization request schema"""
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")


class OIDCCallbackRequest(BaseModel):
    """OIDC callback request schema"""
    code: str = Field(..., description="Authorization code")
    state: Optional[str] = Field(None, description="State parameter")
    redirect_uri: str = Field(..., description="OAuth redirect URI")


class OIDCCallbackResponse(BaseModel):
    """OIDC callback response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    requires_password_change: bool = False

