"""Deployment schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class DeploymentCreate(BaseModel):
    """Deployment creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    template_id: UUID
    template_version: int = Field(..., ge=1)
    gateway_id: Optional[UUID] = None  # None = all gateways
    rollout_strategy: str = Field(default="immediate", pattern="^(immediate|canary|staged)$")
    canary_percentage: Optional[int] = Field(None, ge=1, le=100)
    metadata: Optional[dict] = None


class DeploymentUpdate(BaseModel):
    """Deployment update schema."""
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|failed|rolled_back)$")
    error_message: Optional[str] = None
    metadata: Optional[dict] = None


class DeploymentResponse(BaseModel):
    """Deployment response."""
    id: UUID
    org_id: UUID
    name: str
    template_id: UUID
    template_version: int
    gateway_id: Optional[UUID]
    status: str
    rollout_strategy: str
    canary_percentage: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
