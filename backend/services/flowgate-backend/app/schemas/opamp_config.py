"""Pydantic schemas for OpAMP config management"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ValidationErrorSchema(BaseModel):
    """Validation error schema"""
    level: str = Field(..., description="Error level: 'error' or 'warning'")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field path where error occurred")
    line: Optional[int] = Field(None, description="Line number if applicable")


class ConfigValidationResult(BaseModel):
    """YAML validation result"""
    is_valid: bool = Field(..., description="Whether config is valid")
    errors: List[ValidationErrorSchema] = Field(default_factory=list, description="Validation errors")
    warnings: List[ValidationErrorSchema] = Field(default_factory=list, description="Validation warnings")


class OpAMPConfigDeploymentCreate(BaseModel):
    """Schema for creating OpAMP config deployment"""
    name: str = Field(..., description="Deployment name")
    config_yaml: str = Field(..., description="YAML configuration content")
    rollout_strategy: str = Field(default="immediate", description="Rollout strategy: immediate, canary, staged")
    canary_percentage: Optional[int] = Field(None, ge=0, le=100, description="Canary percentage (0-100)")
    target_tags: Optional[List[str]] = Field(None, description="List of tag names to target (None = all agents)")
    ignore_failures: bool = Field(default=False, description="Skip validation failures")
    template_id: Optional[UUID] = Field(None, description="Optional template ID")
    template_version: Optional[int] = Field(None, description="Optional template version")


class OpAMPConfigDeploymentResponse(BaseModel):
    """Schema for OpAMP config deployment response"""
    id: UUID
    name: str
    config_version: int
    config_hash: str
    template_id: Optional[UUID]
    template_version: Optional[int]
    org_id: UUID
    rollout_strategy: str
    canary_percentage: Optional[int]
    target_tags: Optional[List[str]]
    status: str
    ignore_failures: bool
    created_by: Optional[UUID]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class OpAMPConfigPushRequest(BaseModel):
    """Schema for direct config push request"""
    config_yaml: str = Field(..., description="YAML configuration content")
    gateway_ids: Optional[List[UUID]] = Field(None, description="List of gateway IDs (None = all)")
    target_tags: Optional[List[str]] = Field(None, description="List of tag names to target")
    ignore_failures: bool = Field(default=False, description="Skip validation failures")


class AgentStatusBreakdown(BaseModel):
    """Agent status breakdown for deployment"""
    gateway_id: UUID
    gateway_name: str
    instance_id: str
    status: str
    status_reported_at: Optional[datetime]
    error_message: Optional[str]


class DeploymentProgress(BaseModel):
    """Deployment progress metrics"""
    total: int
    applied: int
    applying: int
    failed: int
    pending: int
    success_rate: float


class ConfigDeploymentStatus(BaseModel):
    """Deployment status with agent breakdown"""
    deployment_id: UUID
    deployment_name: str
    config_version: int
    status: str
    rollout_strategy: str
    canary_percentage: Optional[int]
    target_tags: Optional[List[str]]
    progress: DeploymentProgress
    agent_statuses: List[AgentStatusBreakdown]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class ConfigAuditEntry(BaseModel):
    """Audit log entry"""
    audit_id: UUID
    gateway_id: UUID
    gateway_name: Optional[str]
    instance_id: Optional[str]
    config_version: int
    config_hash: str
    status: str
    status_reported_at: Optional[datetime]
    error_message: Optional[str]
    effective_config_hash: Optional[str]
    created_at: datetime
    updated_at: datetime


class AgentConfigHistoryEntry(BaseModel):
    """Config history entry for an agent"""
    audit_id: UUID
    deployment_id: UUID
    deployment_name: Optional[str]
    config_version: int
    config_hash: str
    status: str
    status_reported_at: Optional[datetime]
    error_message: Optional[str]
    effective_config_hash: Optional[str]
    created_at: datetime


class AgentTagRequest(BaseModel):
    """Schema for adding/removing agent tag"""
    tag: str = Field(..., description="Tag name")


class AgentTagResponse(BaseModel):
    """Schema for agent tag response"""
    id: UUID
    gateway_id: UUID
    tag: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class TagInfo(BaseModel):
    """Tag information with count"""
    tag: str
    count: int


class BulkTagRequest(BaseModel):
    """Schema for bulk tagging operations"""
    gateway_ids: List[UUID] = Field(..., description="List of gateway IDs")
    tags: List[str] = Field(..., description="List of tags to add")


class BulkRemoveTagRequest(BaseModel):
    """Schema for bulk tag removal"""
    gateway_ids: List[UUID] = Field(..., description="List of gateway IDs")
    tags: List[str] = Field(..., description="List of tags to remove")

