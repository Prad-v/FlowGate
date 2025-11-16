"""Package schemas for OpAMP package management"""

from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.agent_package import PackageStatus, PackageType


class PackageBase(BaseModel):
    """Base package schema"""
    package_name: str = Field(..., description="Package name")
    package_version: Optional[str] = Field(None, description="Package version")
    package_type: PackageType = Field(PackageType.TOP_LEVEL, description="Package type")
    download_url: str = Field(..., description="URL to download the package")
    content_hash: Optional[str] = Field(None, description="Content hash of the package")
    signature: Optional[str] = Field(None, description="Package signature (hex encoded)")


class PackageCreate(PackageBase):
    """Schema for creating a package offer"""
    pass


class PackageUpdate(BaseModel):
    """Schema for updating a package"""
    package_version: Optional[str] = None
    download_url: Optional[str] = None
    content_hash: Optional[str] = None
    signature: Optional[str] = None


class PackageResponse(PackageBase):
    """Schema for package response"""
    id: UUID
    gateway_id: UUID
    org_id: UUID
    package_hash: Optional[str] = None
    status: PackageStatus
    installed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    server_offered_hash: Optional[str] = None
    agent_reported_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PackageStatusUpdate(BaseModel):
    """Schema for updating package status from agent"""
    status: PackageStatus
    agent_reported_hash: Optional[str] = None
    error_message: Optional[str] = None

