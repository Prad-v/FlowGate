"""MCP Server Router

API endpoints for managing Model Context Protocol servers.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.utils.auth import get_current_user_org_id
from app.schemas.mcp_server import (
    MCPServerCreate,
    MCPServerUpdate,
    MCPServerResponse,
    MCPServerListResponse,
    MCPConnectionTestResponse,
    MCPResourceDiscoveryResponse,
    MCPServerTypeInfo,
)
from app.services.mcp_server_service import MCPServerService

router = APIRouter(prefix="/settings/mcp", tags=["MCP Servers"])


@router.get("/servers", response_model=MCPServerListResponse)
async def list_servers(
    server_type: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    scope: Optional[str] = None,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """List all MCP servers with optional filters"""
    service = MCPServerService(db)
    servers = service.get_servers(org_id, server_type, is_enabled, scope)
    
    # Mask sensitive data in responses
    masked_servers = []
    for server in servers:
        server_dict = {
            "id": server.id,
            "org_id": server.org_id,
            "server_type": server.server_type.value,
            "server_name": server.server_name,
            "endpoint_url": server.endpoint_url,
            "auth_type": server.auth_type.value,
            "auth_config": service._mask_sensitive_data(server.auth_config) if server.auth_config else None,
            "scope": server.scope.value,
            "is_enabled": server.is_enabled,
            "is_active": server.is_active,
            "last_tested_at": server.last_tested_at,
            "last_test_status": server.last_test_status,
            "last_test_error": server.last_test_error,
            "discovered_resources": server.discovered_resources,
            "metadata": server.server_metadata,
            "created_at": server.created_at,
            "updated_at": server.updated_at,
        }
        masked_servers.append(MCPServerResponse(**server_dict))
    
    return MCPServerListResponse(servers=masked_servers, total=len(masked_servers))


@router.get("/servers/{server_id}", response_model=MCPServerResponse)
async def get_server(
    server_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get a single MCP server by ID"""
    service = MCPServerService(db)
    server = service.get_server(org_id, server_id)
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found"
        )
    
    # Mask sensitive data
    server_dict = {
        "id": server.id,
        "org_id": server.org_id,
        "server_type": server.server_type.value,
        "server_name": server.server_name,
        "endpoint_url": server.endpoint_url,
        "auth_type": server.auth_type.value,
        "auth_config": service._mask_sensitive_data(server.auth_config) if server.auth_config else None,
        "scope": server.scope.value,
        "is_enabled": server.is_enabled,
        "is_active": server.is_active,
        "last_tested_at": server.last_tested_at,
        "last_test_status": server.last_test_status,
        "last_test_error": server.last_test_error,
        "discovered_resources": server.discovered_resources,
        "metadata": server.metadata,
        "created_at": server.created_at,
        "updated_at": server.updated_at,
    }
    
    return MCPServerResponse(**server_dict)


@router.post("/servers", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: MCPServerCreate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Create a new MCP server"""
    service = MCPServerService(db)
    
    try:
        server = service.create_server(org_id, server_data.model_dump())
        
        # Mask sensitive data in response
        server_dict = {
            "id": server.id,
            "org_id": server.org_id,
            "server_type": server.server_type.value,
            "server_name": server.server_name,
            "endpoint_url": server.endpoint_url,
            "auth_type": server.auth_type.value,
            "auth_config": service._mask_sensitive_data(server.auth_config) if server.auth_config else None,
            "scope": server.scope.value,
            "is_enabled": server.is_enabled,
            "is_active": server.is_active,
            "last_tested_at": server.last_tested_at,
            "last_test_status": server.last_test_status,
            "last_test_error": server.last_test_error,
            "discovered_resources": server.discovered_resources,
            "metadata": server.server_metadata,
            "created_at": server.created_at,
            "updated_at": server.updated_at,
        }
        
        return MCPServerResponse(**server_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create MCP server: {str(e)}"
        )


@router.put("/servers/{server_id}", response_model=MCPServerResponse)
async def update_server(
    server_id: UUID,
    server_data: MCPServerUpdate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Update an existing MCP server"""
    service = MCPServerService(db)
    
    try:
        # Only include non-None fields in update
        update_data = {k: v for k, v in server_data.model_dump().items() if v is not None}
        
        server = service.update_server(org_id, server_id, update_data)
        
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP server not found"
            )
        
        # Mask sensitive data in response
        server_dict = {
            "id": server.id,
            "org_id": server.org_id,
            "server_type": server.server_type.value,
            "server_name": server.server_name,
            "endpoint_url": server.endpoint_url,
            "auth_type": server.auth_type.value,
            "auth_config": service._mask_sensitive_data(server.auth_config) if server.auth_config else None,
            "scope": server.scope.value,
            "is_enabled": server.is_enabled,
            "is_active": server.is_active,
            "last_tested_at": server.last_tested_at,
            "last_test_status": server.last_test_status,
            "last_test_error": server.last_test_error,
            "discovered_resources": server.discovered_resources,
            "metadata": server.server_metadata,
            "created_at": server.created_at,
            "updated_at": server.updated_at,
        }
        
        return MCPServerResponse(**server_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update MCP server: {str(e)}"
        )


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Delete an MCP server"""
    service = MCPServerService(db)
    
    success = service.delete_server(org_id, server_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found"
        )


@router.post("/servers/{server_id}/test", response_model=MCPConnectionTestResponse)
async def test_connection(
    server_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Test connection to an MCP server"""
    service = MCPServerService(db)
    
    result = service.test_connection(org_id, server_id)
    
    return MCPConnectionTestResponse(
        success=result.get("success", False),
        message=result.get("message", "Connection test completed"),
        discovered_resources=result.get("discovered_resources"),
        error=result.get("error")
    )


@router.post("/servers/{server_id}/discover", response_model=MCPResourceDiscoveryResponse)
async def discover_resources(
    server_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Discover available resources from an MCP server"""
    service = MCPServerService(db)
    
    result = service.discover_resources(org_id, server_id)
    
    return MCPResourceDiscoveryResponse(
        success=result.get("success", False),
        resources=result.get("resources", {}),
        message=result.get("message"),
        error=result.get("error")
    )


@router.post("/servers/{server_id}/enable", response_model=MCPServerResponse)
async def enable_server(
    server_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Enable an MCP server"""
    service = MCPServerService(db)
    
    server = service.enable_server(org_id, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found"
        )
    
    # Mask sensitive data in response
    server_dict = {
        "id": server.id,
        "org_id": server.org_id,
        "server_type": server.server_type.value,
        "server_name": server.server_name,
        "endpoint_url": server.endpoint_url,
        "auth_type": server.auth_type.value,
        "auth_config": service._mask_sensitive_data(server.auth_config) if server.auth_config else None,
        "scope": server.scope.value,
        "is_enabled": server.is_enabled,
        "is_active": server.is_active,
        "last_tested_at": server.last_tested_at,
        "last_test_status": server.last_test_status,
        "last_test_error": server.last_test_error,
        "discovered_resources": server.discovered_resources,
        "metadata": server.metadata,
        "created_at": server.created_at,
        "updated_at": server.updated_at,
    }
    
    return MCPServerResponse(**server_dict)


@router.post("/servers/{server_id}/disable", response_model=MCPServerResponse)
async def disable_server(
    server_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Disable an MCP server"""
    service = MCPServerService(db)
    
    server = service.disable_server(org_id, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found"
        )
    
    # Mask sensitive data in response
    server_dict = {
        "id": server.id,
        "org_id": server.org_id,
        "server_type": server.server_type.value,
        "server_name": server.server_name,
        "endpoint_url": server.endpoint_url,
        "auth_type": server.auth_type.value,
        "auth_config": service._mask_sensitive_data(server.auth_config) if server.auth_config else None,
        "scope": server.scope.value,
        "is_enabled": server.is_enabled,
        "is_active": server.is_active,
        "last_tested_at": server.last_tested_at,
        "last_test_status": server.last_test_status,
        "last_test_error": server.last_test_error,
        "discovered_resources": server.discovered_resources,
        "metadata": server.metadata,
        "created_at": server.created_at,
        "updated_at": server.updated_at,
    }
    
    return MCPServerResponse(**server_dict)


@router.get("/servers/types", response_model=List[MCPServerTypeInfo])
async def get_server_types():
    """Get available MCP server types and their configuration requirements"""
    return [
        MCPServerTypeInfo(
            server_type="grafana",
            display_name="Grafana",
            description="Connect to Grafana instance for dashboard and alert management",
            required_fields=["endpoint_url", "auth_config"],
            optional_fields=["scope", "metadata"],
            auth_types=["oauth", "custom_header", "no_auth"],
            example_config={
                "endpoint_url": "https://grafana.example.com",
                "auth_type": "custom_header",
                "auth_config": {
                    "token": "your-grafana-api-token"
                }
            }
        ),
        MCPServerTypeInfo(
            server_type="aws",
            display_name="Amazon Web Services",
            description="Connect to AWS for cloud resource management",
            required_fields=["metadata.region", "auth_config.access_key_id", "auth_config.secret_access_key"],
            optional_fields=["auth_config.session_token", "scope"],
            auth_types=["custom_header"],
            example_config={
                "metadata": {
                    "region": "us-east-1"
                },
                "auth_config": {
                    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                }
            }
        ),
        MCPServerTypeInfo(
            server_type="gcp",
            display_name="Google Cloud Platform",
            description="Connect to GCP for cloud resource management",
            required_fields=["metadata.project_id", "auth_config.service_account_key"],
            optional_fields=["scope"],
            auth_types=["custom_header"],
            example_config={
                "metadata": {
                    "project_id": "my-gcp-project"
                },
                "auth_config": {
                    "service_account_key": {
                        "type": "service_account",
                        "project_id": "my-gcp-project",
                        "private_key_id": "...",
                        "private_key": "...",
                        "client_email": "...",
                        "client_id": "...",
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                }
            }
        ),
        MCPServerTypeInfo(
            server_type="custom",
            display_name="Custom MCP Server",
            description="Connect to a custom MCP-compatible server",
            required_fields=["endpoint_url"],
            optional_fields=["auth_config", "scope", "metadata"],
            auth_types=["oauth", "custom_header", "no_auth"],
            example_config={
                "endpoint_url": "https://mcp-server.example.com",
                "auth_type": "custom_header",
                "auth_config": {
                    "token": "your-api-token"
                }
            }
        ),
    ]

