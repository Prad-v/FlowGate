"""Gateway schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class GatewayCreate(BaseModel):
    """Gateway creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    instance_id: str = Field(..., min_length=1, max_length=255)
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GatewayUpdate(BaseModel):
    """Gateway update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, pattern="^(online|offline|unknown)$")
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    version: Optional[str] = None
    config_version: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class GatewayResponse(BaseModel):
    """Gateway response."""
    id: UUID
    org_id: UUID
    name: str
    instance_id: str
    hostname: Optional[str]
    ip_address: Optional[str]
    status: str
    last_seen: Optional[datetime]
    version: Optional[str]
    config_version: int
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GatewayHeartbeat(BaseModel):
    """Gateway heartbeat."""
    instance_id: str
    status: str = "online"
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
