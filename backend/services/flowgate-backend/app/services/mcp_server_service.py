"""MCP Server Service

Service for managing Model Context Protocol servers.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import httpx
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.auth.exceptions import GoogleAuthError

from app.models.mcp_server import MCPServer, MCPServerType, MCPAuthType, MCPScope


class MCPServerService:
    """Service for managing MCP servers"""

    def __init__(self, db: Session):
        self.db = db

    def get_servers(
        self,
        org_id: UUID,
        server_type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        scope: Optional[str] = None
    ) -> List[MCPServer]:
        """Get list of MCP servers with optional filters"""
        query = self.db.query(MCPServer).filter(MCPServer.org_id == org_id)

        if server_type:
            query = query.filter(MCPServer.server_type == server_type)
        if is_enabled is not None:
            query = query.filter(MCPServer.is_enabled == is_enabled)
        if scope:
            query = query.filter(MCPServer.scope == scope)

        return query.order_by(MCPServer.created_at.desc()).all()

    def get_server(self, org_id: UUID, server_id: UUID) -> Optional[MCPServer]:
        """Get a single MCP server by ID"""
        return self.db.query(MCPServer).filter(
            and_(
                MCPServer.id == server_id,
                MCPServer.org_id == org_id
            )
        ).first()

    def create_server(self, org_id: UUID, server_data: Dict[str, Any]) -> MCPServer:
        """Create a new MCP server"""
        # Validate server configuration
        self._validate_server_config(server_data.get("server_type"), server_data)

        # Mask sensitive data in auth_config before storing
        auth_config = server_data.get("auth_config")
        if auth_config:
            auth_config = self._mask_sensitive_data_for_storage(auth_config.copy())

        server = MCPServer(
            org_id=org_id,
            server_type=server_data["server_type"],
            server_name=server_data["server_name"],
            endpoint_url=server_data.get("endpoint_url"),
            auth_type=server_data.get("auth_type", "no_auth"),
            auth_config=auth_config,
            scope=server_data.get("scope", "personal"),
            is_enabled=server_data.get("is_enabled", False),
            server_metadata=server_data.get("metadata"),
        )

        self.db.add(server)
        self.db.commit()
        self.db.refresh(server)
        return server

    def update_server(self, org_id: UUID, server_id: UUID, server_data: Dict[str, Any]) -> Optional[MCPServer]:
        """Update an existing MCP server"""
        server = self.get_server(org_id, server_id)
        if not server:
            return None

        # Validate updated configuration
        server_type = server_data.get("server_type", server.server_type)
        self._validate_server_config(server_type, server_data)

        # Update fields
        if "server_name" in server_data:
            server.server_name = server_data["server_name"]
        if "endpoint_url" in server_data:
            server.endpoint_url = server_data["endpoint_url"]
        if "auth_type" in server_data:
            server.auth_type = server_data["auth_type"]
        if "auth_config" in server_data:
            # Mask sensitive data before storing
            auth_config = server_data["auth_config"]
            if auth_config:
                auth_config = self._mask_sensitive_data_for_storage(auth_config.copy())
            server.auth_config = auth_config
        if "scope" in server_data:
            server.scope = server_data["scope"]
        if "metadata" in server_data:
            server.server_metadata = server_data["metadata"]

        server.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(server)
        return server

    def delete_server(self, org_id: UUID, server_id: UUID) -> bool:
        """Delete an MCP server"""
        server = self.get_server(org_id, server_id)
        if not server:
            return False

        self.db.delete(server)
        self.db.commit()
        return True

    def test_connection(self, org_id: UUID, server_id: UUID) -> Dict[str, Any]:
        """Test connection to an MCP server and discover resources"""
        server = self.get_server(org_id, server_id)
        if not server:
            return {"success": False, "message": "Server not found", "discovered_resources": None, "error": None}

        try:
            # Unmask auth_config for testing
            auth_config = self._unmask_sensitive_data(server.auth_config) if server.auth_config else {}

            if server.server_type == MCPServerType.GRAFANA:
                result = self._test_grafana_connection(server.endpoint_url, auth_config)
            elif server.server_type == MCPServerType.AWS:
                result = self._test_aws_connection(server.server_metadata, auth_config)
            elif server.server_type == MCPServerType.GCP:
                result = self._test_gcp_connection(server.server_metadata, auth_config)
            elif server.server_type == MCPServerType.CUSTOM:
                result = self._test_custom_connection(server.endpoint_url, auth_config)
            else:
                result = {"success": False, "message": f"Unknown server type: {server.server_type}", "discovered_resources": None}

            # Update server status
            server.is_active = result.get("success", False)
            server.last_tested_at = datetime.utcnow()
            server.last_test_status = "success" if result.get("success") else "failed"
            server.last_test_error = result.get("error")
            if result.get("discovered_resources"):
                server.discovered_resources = result["discovered_resources"]

            self.db.commit()
            return result

        except Exception as e:
            server.is_active = False
            server.last_tested_at = datetime.utcnow()
            server.last_test_status = "error"
            server.last_test_error = str(e)
            self.db.commit()
            return {"success": False, "message": f"Connection test failed: {str(e)}", "discovered_resources": None, "error": str(e)}

    def discover_resources(self, org_id: UUID, server_id: UUID) -> Dict[str, Any]:
        """Discover available resources/tools from an MCP server"""
        server = self.get_server(org_id, server_id)
        if not server:
            return {"success": False, "resources": {}, "message": "Server not found", "error": None}

        try:
            # Unmask auth_config for discovery
            auth_config = self._unmask_sensitive_data(server.auth_config) if server.auth_config else {}

            if server.server_type == MCPServerType.GRAFANA:
                resources = self._discover_grafana_resources(server.endpoint_url, auth_config)
            elif server.server_type == MCPServerType.AWS:
                resources = self._discover_aws_resources(server.server_metadata, auth_config)
            elif server.server_type == MCPServerType.GCP:
                resources = self._discover_gcp_resources(server.server_metadata, auth_config)
            elif server.server_type == MCPServerType.CUSTOM:
                resources = self._discover_custom_resources(server.endpoint_url, auth_config)
            else:
                return {"success": False, "resources": {}, "message": f"Unknown server type: {server.server_type}", "error": None}

            # Update discovered resources
            server.discovered_resources = resources
            server.updated_at = datetime.utcnow()
            self.db.commit()

            return {"success": True, "resources": resources, "message": "Resources discovered successfully", "error": None}

        except Exception as e:
            return {"success": False, "resources": {}, "message": f"Resource discovery failed: {str(e)}", "error": str(e)}

    def enable_server(self, org_id: UUID, server_id: UUID) -> Optional[MCPServer]:
        """Enable an MCP server"""
        server = self.get_server(org_id, server_id)
        if not server:
            return None

        server.is_enabled = True
        server.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(server)
        return server

    def disable_server(self, org_id: UUID, server_id: UUID) -> Optional[MCPServer]:
        """Disable an MCP server"""
        server = self.get_server(org_id, server_id)
        if not server:
            return None

        server.is_enabled = False
        server.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(server)
        return server

    def _validate_server_config(self, server_type: str, config: Dict[str, Any]) -> None:
        """Validate server-specific configuration"""
        if server_type == "grafana":
            if not config.get("endpoint_url"):
                raise ValueError("endpoint_url is required for Grafana servers")
            if config.get("auth_type") in ["oauth", "custom_header"] and not config.get("auth_config"):
                raise ValueError("auth_config is required when auth_type is oauth or custom_header")
        
        elif server_type == "aws":
            if not config.get("metadata", {}).get("region"):
                raise ValueError("region is required in metadata for AWS servers")
            auth_config = config.get("auth_config", {})
            if not auth_config.get("access_key_id") or not auth_config.get("secret_access_key"):
                raise ValueError("access_key_id and secret_access_key are required in auth_config for AWS servers")
        
        elif server_type == "gcp":
            if not config.get("metadata", {}).get("project_id"):
                raise ValueError("project_id is required in metadata for GCP servers")
            auth_config = config.get("auth_config", {})
            if not auth_config.get("service_account_key"):
                raise ValueError("service_account_key is required in auth_config for GCP servers")
        
        elif server_type == "custom":
            if not config.get("endpoint_url"):
                raise ValueError("endpoint_url is required for custom servers")

    def _test_grafana_connection(self, endpoint: str, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection to Grafana server"""
        try:
            headers = {}
            if auth_config.get("auth_type") == "custom_header":
                token = auth_config.get("token") or auth_config.get("api_key")
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            with httpx.Client(timeout=10.0) as client:
                # Test Grafana API health endpoint
                health_url = f"{endpoint.rstrip('/')}/api/health"
                response = client.get(health_url, headers=headers)
                
                if response.status_code == 200:
                    # Discover resources
                    resources = self._discover_grafana_resources(endpoint, auth_config)
                    return {
                        "success": True,
                        "message": "Connection successful",
                        "discovered_resources": resources,
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Connection failed: HTTP {response.status_code}",
                        "discovered_resources": None,
                        "error": f"HTTP {response.status_code}: {response.text[:200]}"
                    }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "discovered_resources": None,
                "error": str(e)
            }

    def _test_aws_connection(self, metadata: Optional[Dict[str, Any]], auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection to AWS"""
        try:
            region = metadata.get("region") if metadata else None
            if not region:
                return {
                    "success": False,
                    "message": "AWS region is required",
                    "discovered_resources": None,
                    "error": "Missing region in metadata"
                }

            access_key = auth_config.get("access_key_id")
            secret_key = auth_config.get("secret_access_key")
            session_token = auth_config.get("session_token")

            if not access_key or not secret_key:
                return {
                    "success": False,
                    "message": "AWS credentials are required",
                    "discovered_resources": None,
                    "error": "Missing access_key_id or secret_access_key"
                }

            # Test AWS connection using STS
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token,
                region_name=region
            )

            # Get caller identity to test credentials
            identity = sts_client.get_caller_identity()
            
            # Discover resources
            resources = self._discover_aws_resources(metadata, auth_config)
            
            return {
                "success": True,
                "message": f"Connection successful. Account: {identity.get('Account', 'Unknown')}",
                "discovered_resources": resources,
                "error": None
            }

        except NoCredentialsError:
            return {
                "success": False,
                "message": "AWS credentials not found",
                "discovered_resources": None,
                "error": "No credentials provided"
            }
        except ClientError as e:
            return {
                "success": False,
                "message": f"AWS connection failed: {e.response.get('Error', {}).get('Message', str(e))}",
                "discovered_resources": None,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"AWS connection test failed: {str(e)}",
                "discovered_resources": None,
                "error": str(e)
            }

    def _test_gcp_connection(self, metadata: Optional[Dict[str, Any]], auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection to GCP"""
        try:
            project_id = metadata.get("project_id") if metadata else None
            if not project_id:
                return {
                    "success": False,
                    "message": "GCP project_id is required",
                    "discovered_resources": None,
                    "error": "Missing project_id in metadata"
                }

            service_account_key = auth_config.get("service_account_key")
            if not service_account_key:
                return {
                    "success": False,
                    "message": "GCP service account key is required",
                    "discovered_resources": None,
                    "error": "Missing service_account_key in auth_config"
                }

            # Parse service account key
            if isinstance(service_account_key, str):
                key_data = json.loads(service_account_key)
            else:
                key_data = service_account_key

            # Create credentials
            credentials = service_account.Credentials.from_service_account_info(
                key_data,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )

            # Refresh credentials to test
            credentials.refresh(Request())

            # Discover resources
            resources = self._discover_gcp_resources(metadata, auth_config)

            return {
                "success": True,
                "message": f"Connection successful. Project: {project_id}",
                "discovered_resources": resources,
                "error": None
            }

        except json.JSONDecodeError:
            return {
                "success": False,
                "message": "Invalid service account key JSON",
                "discovered_resources": None,
                "error": "Invalid JSON format"
            }
        except GoogleAuthError as e:
            return {
                "success": False,
                "message": f"GCP authentication failed: {str(e)}",
                "discovered_resources": None,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"GCP connection test failed: {str(e)}",
                "discovered_resources": None,
                "error": str(e)
            }

    def _test_custom_connection(self, endpoint: str, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection to custom MCP server"""
        try:
            headers = {}
            if auth_config.get("auth_type") == "custom_header":
                token = auth_config.get("token") or auth_config.get("api_key")
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            with httpx.Client(timeout=10.0) as client:
                # Try MCP protocol health/discovery endpoint
                health_url = f"{endpoint.rstrip('/')}/health"
                try:
                    response = client.get(health_url, headers=headers)
                    if response.status_code == 200:
                        resources = self._discover_custom_resources(endpoint, auth_config)
                        return {
                            "success": True,
                            "message": "Connection successful",
                            "discovered_resources": resources,
                            "error": None
                        }
                except httpx.RequestError:
                    pass

                # Fallback: try root endpoint
                response = client.get(endpoint, headers=headers, follow_redirects=True)
                if response.status_code < 500:
                    resources = self._discover_custom_resources(endpoint, auth_config)
                    return {
                        "success": True,
                        "message": "Connection successful",
                        "discovered_resources": resources,
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Connection failed: HTTP {response.status_code}",
                        "discovered_resources": None,
                        "error": f"HTTP {response.status_code}"
                    }

        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "discovered_resources": None,
                "error": str(e)
            }

    def _discover_grafana_resources(self, endpoint: str, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """Discover Grafana resources (dashboards, alerts, data sources)"""
        resources = {
            "dashboards": [],
            "alerts": [],
            "data_sources": []
        }

        try:
            headers = {}
            if auth_config.get("auth_type") == "custom_header":
                token = auth_config.get("token") or auth_config.get("api_key")
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            with httpx.Client(timeout=10.0) as client:
                base_url = endpoint.rstrip('/')

                # Discover dashboards
                try:
                    dashboards_url = f"{base_url}/api/search?type=dash-db"
                    response = client.get(dashboards_url, headers=headers)
                    if response.status_code == 200:
                        dashboards = response.json()
                        resources["dashboards"] = [
                            {"uid": d.get("uid"), "title": d.get("title"), "url": d.get("url")}
                            for d in dashboards[:50]  # Limit to 50
                        ]
                except Exception:
                    pass

                # Discover data sources
                try:
                    datasources_url = f"{base_url}/api/datasources"
                    response = client.get(datasources_url, headers=headers)
                    if response.status_code == 200:
                        datasources = response.json()
                        resources["data_sources"] = [
                            {"id": ds.get("id"), "name": ds.get("name"), "type": ds.get("type")}
                            for ds in datasources
                        ]
                except Exception:
                    pass

                # Discover alerts (if Alerting API is available)
                try:
                    alerts_url = f"{base_url}/api/ruler/grafana/api/v1/rules"
                    response = client.get(alerts_url, headers=headers)
                    if response.status_code == 200:
                        alerts_data = response.json()
                        # Flatten alert rules
                        alerts = []
                        for group in alerts_data.values():
                            for rule_group in group:
                                for rule in rule_group.get("rules", []):
                                    alerts.append({
                                        "name": rule.get("alert"),
                                        "state": rule.get("state"),
                                        "expr": rule.get("expr")
                                    })
                        resources["alerts"] = alerts[:50]  # Limit to 50
                except Exception:
                    pass

        except Exception:
            pass

        return resources

    def _discover_aws_resources(self, metadata: Optional[Dict[str, Any]], auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """Discover AWS resources based on available services"""
        resources = {
            "services": [],
            "regions": []
        }

        try:
            region = metadata.get("region") if metadata else "us-east-1"
            access_key = auth_config.get("access_key_id")
            secret_key = auth_config.get("secret_access_key")
            session_token = auth_config.get("session_token")

            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token,
                region_name=region
            )

            # Get available services
            available_services = session.get_available_services()
            resources["services"] = sorted(available_services)[:50]  # Limit to 50

            # Get available regions
            available_regions = session.get_available_regions('ec2')
            resources["regions"] = available_regions[:20]  # Limit to 20

        except Exception:
            pass

        return resources

    def _discover_gcp_resources(self, metadata: Optional[Dict[str, Any]], auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """Discover GCP resources"""
        resources = {
            "services": [],
            "projects": []
        }

        try:
            project_id = metadata.get("project_id") if metadata else None
            service_account_key = auth_config.get("service_account_key")

            if isinstance(service_account_key, str):
                key_data = json.loads(service_account_key)
            else:
                key_data = service_account_key

            credentials = service_account.Credentials.from_service_account_info(
                key_data,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )

            # List available GCP services (common ones)
            resources["services"] = [
                "compute", "storage", "bigquery", "pubsub", "cloudfunctions",
                "cloudrun", "gke", "cloudsql", "monitoring", "logging"
            ]

            if project_id:
                resources["projects"] = [project_id]

        except Exception:
            pass

        return resources

    def _discover_custom_resources(self, endpoint: str, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """Discover resources from custom MCP server"""
        resources = {
            "tools": [],
            "resources": []
        }

        try:
            headers = {}
            if auth_config.get("auth_type") == "custom_header":
                token = auth_config.get("token") or auth_config.get("api_key")
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            with httpx.Client(timeout=10.0) as client:
                # Try MCP protocol discovery endpoint
                discovery_url = f"{endpoint.rstrip('/')}/mcp/discover"
                try:
                    response = client.get(discovery_url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        resources["tools"] = data.get("tools", [])
                        resources["resources"] = data.get("resources", [])
                except Exception:
                    pass

        except Exception:
            pass

        return resources

    def _mask_sensitive_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in configuration for API responses"""
        masked = config.copy()
        
        # Mask API keys, tokens, and secrets
        sensitive_keys = ["api_key", "token", "access_key_id", "secret_access_key", "session_token", "service_account_key"]
        
        for key in sensitive_keys:
            if key in masked and masked[key]:
                value = masked[key]
                if isinstance(value, str) and len(value) > 4:
                    masked[key] = "*" * (len(value) - 4) + value[-4:]
                elif isinstance(value, dict):
                    # For service account keys, mask the private_key
                    if "private_key" in value:
                        pk = value["private_key"]
                        if isinstance(pk, str) and len(pk) > 4:
                            masked[key] = {**value, "private_key": "*" * (len(pk) - 4) + pk[-4:]}
        
        return masked

    def _mask_sensitive_data_for_storage(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare sensitive data for storage (encryption would be added here)"""
        # For now, store as-is. In production, encrypt sensitive fields
        return config

    def _unmask_sensitive_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Unmask sensitive data for use (decryption would be added here)"""
        # For now, return as-is. In production, decrypt sensitive fields
        return config

