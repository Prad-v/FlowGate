"""Gateway schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from app.models.gateway import GatewayStatus


class GatewayBase(BaseModel):
    """Base gateway schema"""

    name: str = Field(..., min_length=1, max_length=255)
    instance_id: str = Field(..., description="OpAMP instance ID")


class GatewayCreate(GatewayBase):
    """Schema for creating a gateway (org_id is extracted from registration token)"""

    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GatewayUpdate(BaseModel):
    """Schema for updating a gateway"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[GatewayStatus] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    current_config_version: Optional[int] = None


class GatewayResponse(GatewayBase):
    """Schema for gateway response"""

    id: UUID
    org_id: UUID
    status: GatewayStatus
    last_seen: datetime | None
    current_config_version: int | None
    metadata: Dict[str, Any] | None
    hostname: str | None
    ip_address: str | None
    opamp_token: Optional[str] = None  # OpAMP access token
    opamp_endpoint: Optional[str] = None  # OpAMP server endpoint
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class GatewayRegistrationResponse(GatewayBase):
    """Schema for gateway registration response (includes OpAMP connection details)"""

    id: UUID
    org_id: UUID
    status: GatewayStatus
    last_seen: datetime | None
    current_config_version: int | None
    metadata: Dict[str, Any] | None
    hostname: str | None
    ip_address: str | None
    opamp_token: str = Field(..., description="OpAMP access token for future communication")
    opamp_endpoint: str = Field(..., description="OpAMP server endpoint URL")
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class AgentHealthResponse(BaseModel):
    """Schema for agent health response"""

    status: str = Field(..., description="Health status: healthy, warning, unhealthy, offline")
    last_seen: Optional[datetime] = None
    seconds_since_last_seen: Optional[int] = None
    uptime_seconds: Optional[int] = None
    health_score: int = Field(..., ge=0, le=100, description="Health score 0-100")


class AgentVersionResponse(BaseModel):
    """Schema for agent version response"""

    agent_version: Optional[str] = None
    otel_version: Optional[str] = None
    capabilities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentConfigResponse(BaseModel):
    """Schema for agent config response"""

    config_yaml: str
    config_version: Optional[int] = None
    deployment_id: Optional[str] = None
    last_updated: Optional[datetime] = None


class AgentMetricsResponse(BaseModel):
    """Schema for agent metrics response"""

    logs_processed: Optional[int] = None
    errors: Optional[int] = None
    latency_ms: Optional[float] = None
    last_updated: Optional[datetime] = None


class AgentStatusResponse(BaseModel):
    """Schema for combined agent status response"""

    gateway_id: UUID
    instance_id: str
    name: str
    health: AgentHealthResponse
    version: AgentVersionResponse
    config: Optional[AgentConfigResponse] = None
    metrics: Optional[AgentMetricsResponse] = None

