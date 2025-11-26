"""Organization schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class OrganizationCreate(BaseModel):
    """Organization create schema"""
    name: str = Field(..., description="Organization name")
    slug: str = Field(..., description="Organization slug (URL-friendly)")
    is_active: bool = Field(True, description="Whether organization is active")


class OrganizationUpdate(BaseModel):
    """Organization update schema"""
    name: Optional[str] = None
    slug: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(BaseModel):
    """Organization response schema"""
    id: UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserOrganizationAssociation(BaseModel):
    """User-Organization association schema"""
    user_id: UUID = Field(..., description="User ID")
    org_id: UUID = Field(..., description="Organization ID")

