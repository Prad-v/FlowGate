"""Deployment schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.deployment import DeploymentStatus, RolloutStrategy


class DeploymentBase(BaseModel):
    """Base deployment schema"""

    name: str = Field(..., min_length=1, max_length=255)
    template_id: UUID
    template_version: int
    rollout_strategy: RolloutStrategy = RolloutStrategy.IMMEDIATE
    canary_percentage: int = Field(default=0, ge=0, le=100)


class DeploymentCreate(DeploymentBase):
    """Schema for creating a deployment"""

    org_id: UUID
    gateway_id: Optional[UUID] = Field(None, description="None means all gateways")
    metadata: Optional[Dict[str, Any]] = None


class DeploymentUpdate(BaseModel):
    """Schema for updating a deployment"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[DeploymentStatus] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DeploymentStatusUpdate(BaseModel):
    """Schema for updating deployment status"""

    status: DeploymentStatus
    error_message: Optional[str] = None


class DeploymentResponse(DeploymentBase):
    """Schema for deployment response"""

    id: UUID
    org_id: UUID
    gateway_id: UUID | None
    status: DeploymentStatus
    created_by: UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    metadata: Dict[str, Any] | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}

