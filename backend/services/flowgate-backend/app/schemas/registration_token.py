"""Registration token schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class RegistrationTokenCreate(BaseModel):
    """Schema for creating a registration token"""

    name: Optional[str] = Field(None, max_length=255, description="Optional description for the token")
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650, description="Token expiration in days (1-3650)")


class RegistrationTokenResponse(BaseModel):
    """Schema for registration token response (excludes actual token)"""

    id: UUID
    org_id: UUID
    name: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    created_by: Optional[UUID] = None

    model_config = {"from_attributes": True}


class RegistrationTokenCreateResponse(BaseModel):
    """Schema for registration token creation response (includes plain token)"""

    token: str = Field(..., description="Plain registration token (store securely, shown only once)")
    token_info: RegistrationTokenResponse


class RegistrationTokenListResponse(BaseModel):
    """Schema for listing registration tokens"""

    tokens: list[RegistrationTokenResponse]
    total: int

