"""Tenant/Organization schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class OrganizationCreate(BaseModel):
    """Organization creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None


class OrganizationResponse(BaseModel):
    """Organization response."""
    id: UUID
    name: str
    slug: str
    is_active: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


