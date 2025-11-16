"""Connection Settings schemas for OpAMP connection credential management"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.connection_settings import ConnectionSettingsType, ConnectionSettingsStatus


class ConnectionSettingsBase(BaseModel):
    """Base connection settings schema"""
    settings_type: ConnectionSettingsType = Field(..., description="Type of connection settings")
    settings_name: Optional[str] = Field(None, description="Name for 'other' connection settings")
    settings_data: Dict[str, Any] = Field(default_factory=dict, description="Connection settings data (endpoint, headers, etc.)")
    certificate_pem: Optional[str] = Field(None, description="PEM-encoded certificate")
    private_key_pem: Optional[str] = Field(None, description="PEM-encoded private key")
    ca_cert_pem: Optional[str] = Field(None, description="PEM-encoded CA certificate")


class ConnectionSettingsCreate(ConnectionSettingsBase):
    """Schema for creating connection settings"""
    pass


class ConnectionSettingsUpdate(BaseModel):
    """Schema for updating connection settings"""
    settings_data: Optional[Dict[str, Any]] = None
    certificate_pem: Optional[str] = None
    private_key_pem: Optional[str] = None
    ca_cert_pem: Optional[str] = None


class ConnectionSettingsResponse(ConnectionSettingsBase):
    """Schema for connection settings response"""
    id: UUID
    gateway_id: UUID
    org_id: UUID
    settings_hash: Optional[str] = None
    status: ConnectionSettingsStatus
    applied_at: Optional[datetime] = None
    error_message: Optional[str] = None
    csr_pem: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectionSettingsStatusUpdate(BaseModel):
    """Schema for updating connection settings status from agent"""
    status: ConnectionSettingsStatus
    error_message: Optional[str] = None


class CSRRequest(BaseModel):
    """Schema for Certificate Signing Request"""
    csr_pem: str = Field(..., description="PEM-encoded Certificate Signing Request")
    settings_type: ConnectionSettingsType = Field(ConnectionSettingsType.OPAMP, description="Type of connection settings")

