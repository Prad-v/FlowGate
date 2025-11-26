"""User management schemas"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID


class UserCreate(BaseModel):
    """User create schema"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Username")
    password: Optional[str] = Field(None, description="Password (required for local users)")
    full_name: Optional[str] = Field(None, description="Full name")
    org_id: Optional[UUID] = Field(None, description="Organization ID")
    is_active: bool = Field(True, description="Whether user is active")
    is_superuser: bool = Field(False, description="Whether user is superuser")


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    org_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserOrganizationAssign(BaseModel):
    """Assign user to organization"""
    user_id: UUID = Field(..., description="User ID")
    org_id: UUID = Field(..., description="Organization ID")

