"""MCP Server model for managing Model Context Protocol servers"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import enum
from app.database import Base
from app.models.base import BaseModel


class MCPServerType(str, enum.Enum):
    """MCP Server types"""
    GRAFANA = "grafana"
    AWS = "aws"
    GCP = "gcp"
    CUSTOM = "custom"


class MCPAuthType(str, enum.Enum):
    """MCP Authentication types"""
    OAUTH = "oauth"
    CUSTOM_HEADER = "custom_header"
    NO_AUTH = "no_auth"


class MCPScope(str, enum.Enum):
    """MCP Server scope"""
    PERSONAL = "personal"
    TENANT = "tenant"


class MCPServer(Base, BaseModel):
    """MCP Server model for managing Model Context Protocol servers"""

    __tablename__ = "mcp_servers"

    org_id = Column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    server_type = Column(
        SQLEnum(MCPServerType, name="mcp_server_type", create_type=False),
        nullable=False,
        index=True
    )
    
    server_name = Column(String(255), nullable=False)
    endpoint_url = Column(String(512), nullable=True)  # Not required for AWS/GCP
    
    auth_type = Column(
        SQLEnum(MCPAuthType, name="mcp_auth_type", create_type=False),
        nullable=False,
        default=MCPAuthType.NO_AUTH
    )
    
    # Store auth credentials securely (API keys, tokens, service account keys)
    auth_config = Column(postgresql.JSONB, nullable=True)
    
    scope = Column(
        SQLEnum(MCPScope, name="mcp_scope", create_type=False),
        nullable=False,
        default=MCPScope.PERSONAL
    )
    
    is_enabled = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=False, nullable=False)  # Connection status
    
    last_tested_at = Column(postgresql.TIMESTAMP(timezone=True), nullable=True)
    last_test_status = Column(String(50), nullable=True)  # "success", "failed", "error"
    last_test_error = Column(String(512), nullable=True)
    
    # Discovered resources/tools from the MCP server
    discovered_resources = Column(postgresql.JSONB, nullable=True)
    
    # Additional server-specific configuration (region, project_id, etc.)
    server_metadata = Column(postgresql.JSONB, nullable=True)
    
    # Relationships
    organization = relationship("Organization", backref="mcp_servers")

