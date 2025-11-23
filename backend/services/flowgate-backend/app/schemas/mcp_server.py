"""MCP Server schemas"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List, Literal
from uuid import UUID
from datetime import datetime


class MCPServerConfig(BaseModel):
    """Base MCP server configuration schema"""
    
    server_type: Literal["grafana", "aws", "gcp", "custom"] = Field(..., description="Type of MCP server")
    server_name: str = Field(..., min_length=1, max_length=255, description="User-defined server name")
    endpoint_url: Optional[str] = Field(None, max_length=512, description="MCP server endpoint URL")
    auth_type: Literal["oauth", "custom_header", "no_auth"] = Field(default="no_auth", description="Authentication type")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration (credentials, tokens, etc.)")
    scope: Literal["personal", "tenant"] = Field(default="personal", description="Server scope")
    is_enabled: bool = Field(default=False, description="Whether the server is enabled")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional server-specific configuration")


class MCPServerCreate(BaseModel):
    """Schema for creating a new MCP server"""
    
    server_type: Literal["grafana", "aws", "gcp", "custom"] = Field(..., description="Type of MCP server")
    server_name: str = Field(..., min_length=1, max_length=255, description="User-defined server name")
    endpoint_url: Optional[str] = Field(None, max_length=512, description="MCP server endpoint URL")
    auth_type: Literal["oauth", "custom_header", "no_auth"] = Field(default="no_auth", description="Authentication type")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    scope: Literal["personal", "tenant"] = Field(default="personal", description="Server scope")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional server-specific configuration")


class MCPServerUpdate(BaseModel):
    """Schema for updating an MCP server"""
    
    server_name: Optional[str] = Field(None, min_length=1, max_length=255, description="User-defined server name")
    endpoint_url: Optional[str] = Field(None, max_length=512, description="MCP server endpoint URL")
    auth_type: Optional[Literal["oauth", "custom_header", "no_auth"]] = Field(None, description="Authentication type")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    scope: Optional[Literal["personal", "tenant"]] = Field(None, description="Server scope")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional server-specific configuration")


class MCPServerResponse(BaseModel):
    """Schema for MCP server response"""
    
    id: UUID
    org_id: UUID
    server_type: str
    server_name: str
    endpoint_url: Optional[str] = None
    auth_type: str
    auth_config: Optional[Dict[str, Any]] = None  # Masked in service layer
    scope: str
    is_enabled: bool
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_test_status: Optional[str] = None
    last_test_error: Optional[str] = None
    discovered_resources: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MCPServerListResponse(BaseModel):
    """Schema for list of MCP servers"""
    
    servers: List[MCPServerResponse] = Field(..., description="List of MCP servers")
    total: int = Field(..., description="Total number of servers")


class MCPConnectionTestRequest(BaseModel):
    """Schema for connection test request"""
    
    pass  # Server ID is in path, no body needed


class MCPConnectionTestResponse(BaseModel):
    """Schema for connection test response"""
    
    success: bool = Field(..., description="Whether connection test was successful")
    message: str = Field(..., description="Test result message")
    discovered_resources: Optional[Dict[str, Any]] = Field(None, description="Discovered resources/tools")
    error: Optional[str] = Field(None, description="Error message if test failed")


class MCPResourceDiscoveryResponse(BaseModel):
    """Schema for resource discovery response"""
    
    success: bool = Field(..., description="Whether discovery was successful")
    resources: Dict[str, Any] = Field(..., description="Discovered resources/tools")
    message: Optional[str] = Field(None, description="Discovery result message")
    error: Optional[str] = Field(None, description="Error message if discovery failed")


class MCPServerTypeInfo(BaseModel):
    """Schema for server type information"""
    
    server_type: str = Field(..., description="Server type identifier")
    display_name: str = Field(..., description="Display name for the server type")
    description: str = Field(..., description="Description of the server type")
    required_fields: List[str] = Field(..., description="Required configuration fields")
    optional_fields: List[str] = Field(..., description="Optional configuration fields")
    auth_types: List[str] = Field(..., description="Supported authentication types")
    example_config: Optional[Dict[str, Any]] = Field(None, description="Example configuration")

