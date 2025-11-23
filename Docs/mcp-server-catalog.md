# MCP Server Catalog

The MCP (Model Context Protocol) Server Catalog allows you to configure, test, enable/disable, and discover resources from external services including Grafana, AWS, GCP, and custom MCP-compatible servers.

## Overview

The MCP Server Catalog provides a unified interface for managing connections to external observability and cloud platforms. This enables FlowGate to:

- Configure connections to external services (Grafana, AWS, GCP, custom servers)
- Enable AI features to access external data sources via MCP protocol
- Manage integrations for exporting telemetry to external platforms

## Features

- **Multiple Server Types**: Support for Grafana, AWS, GCP, and custom MCP servers
- **Connection Testing**: Validate server connections before enabling
- **Resource Discovery**: Automatically discover available tools and resources from connected servers
- **Enable/Disable**: Control which servers are active
- **Secure Credential Storage**: Sensitive credentials are masked and stored securely
- **Scope Management**: Configure servers as personal or tenant-wide (shared)

## Accessing the MCP Server Catalog

1. Navigate to **Settings** in the FlowGate UI
2. Click on the **MCP Server Catalog** tab
3. View existing servers or click **Add Server** to create a new one

## Server Types

### Grafana

Connect to a Grafana instance for dashboard and alert management.

**Required Configuration:**
- **Endpoint URL**: Your Grafana instance URL (e.g., `https://grafana.example.com`)
- **Authentication**: 
  - OAuth (if configured)
  - Custom Header with Grafana API token
  - No authentication (for public instances)

**Discovered Resources:**
- Dashboards
- Alerts
- Data Sources

**Example Configuration:**
```json
{
  "server_type": "grafana",
  "server_name": "Production Grafana",
  "endpoint_url": "https://grafana.example.com",
  "auth_type": "custom_header",
  "auth_config": {
    "token": "your-grafana-api-token"
  },
  "scope": "tenant"
}
```

### Amazon Web Services (AWS)

Connect to AWS for cloud resource management and telemetry export.

**Required Configuration:**
- **Region**: AWS region (e.g., `us-east-1`)
- **Access Key ID**: AWS access key
- **Secret Access Key**: AWS secret key
- **Session Token** (optional): For temporary credentials

**Discovered Resources:**
- Available AWS services
- Available regions

**Example Configuration:**
```json
{
  "server_type": "aws",
  "server_name": "AWS Production",
  "metadata": {
    "region": "us-east-1"
  },
  "auth_config": {
    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  },
  "scope": "tenant"
}
```

### Google Cloud Platform (GCP)

Connect to GCP for cloud resource management and telemetry export.

**Required Configuration:**
- **Project ID**: GCP project identifier
- **Service Account Key**: JSON service account key with appropriate permissions

**Discovered Resources:**
- Available GCP services
- Project information

**Example Configuration:**
```json
{
  "server_type": "gcp",
  "server_name": "GCP Production",
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
  },
  "scope": "tenant"
}
```

### Custom MCP Server

Connect to any MCP-compatible server.

**Required Configuration:**
- **Endpoint URL**: MCP server endpoint
- **Authentication**: OAuth, custom header, or no authentication

**Discovered Resources:**
- Tools and resources exposed by the MCP server

**Example Configuration:**
```json
{
  "server_type": "custom",
  "server_name": "Custom MCP Server",
  "endpoint_url": "https://mcp-server.example.com",
  "auth_type": "custom_header",
  "auth_config": {
    "token": "your-api-token"
  },
  "scope": "personal"
}
```

## Managing Servers

### Creating a Server

1. Click **Add Server** in the MCP Server Catalog
2. Select the server type
3. Fill in the required configuration fields
4. Optionally configure authentication
5. Click **Create Server**

### Testing Connection

After creating a server, you can test the connection:

1. Click **Test** next to the server
2. The system will validate credentials and endpoint connectivity
3. If successful, discovered resources will be displayed

### Discovering Resources

To discover available resources from a server:

1. Click **Discover** next to the server
2. The system will query the server for available tools and resources
3. Discovered resources are stored and displayed in an expandable section

### Enabling/Disabling Servers

- **Enable**: Click **Enable** to activate a server
- **Disable**: Click **Disable** to deactivate a server

Only enabled servers are used by FlowGate features.

### Editing Servers

1. Click **Edit** next to the server
2. Modify configuration fields
3. Click **Update Server**

### Deleting Servers

1. Click **Delete** next to the server
2. Confirm deletion

**Warning**: Deleting a server removes all configuration and discovered resources.

## Security Best Practices

1. **Credential Management**:
   - Never share API keys or tokens
   - Use service accounts with minimal required permissions
   - Rotate credentials regularly

2. **Scope Selection**:
   - Use **Personal** scope for individual use
   - Use **Tenant** scope only when the server should be shared across the organization

3. **Authentication**:
   - Prefer OAuth when available
   - Use strong API tokens for custom header authentication
   - Avoid storing credentials in plain text

## API Reference

### List Servers

```http
GET /api/v1/settings/mcp/servers
```

Query Parameters:
- `server_type` (optional): Filter by server type
- `is_enabled` (optional): Filter by enabled status
- `scope` (optional): Filter by scope

### Get Server

```http
GET /api/v1/settings/mcp/servers/{server_id}
```

### Create Server

```http
POST /api/v1/settings/mcp/servers
Content-Type: application/json

{
  "server_type": "grafana",
  "server_name": "My Grafana",
  "endpoint_url": "https://grafana.example.com",
  "auth_type": "custom_header",
  "auth_config": {
    "token": "api-token"
  },
  "scope": "personal"
}
```

### Update Server

```http
PUT /api/v1/settings/mcp/servers/{server_id}
Content-Type: application/json

{
  "server_name": "Updated Name",
  "auth_config": {
    "token": "new-token"
  }
}
```

### Delete Server

```http
DELETE /api/v1/settings/mcp/servers/{server_id}
```

### Test Connection

```http
POST /api/v1/settings/mcp/servers/{server_id}/test
```

### Discover Resources

```http
POST /api/v1/settings/mcp/servers/{server_id}/discover
```

### Enable Server

```http
POST /api/v1/settings/mcp/servers/{server_id}/enable
```

### Disable Server

```http
POST /api/v1/settings/mcp/servers/{server_id}/disable
```

### Get Server Types

```http
GET /api/v1/settings/mcp/servers/types
```

Returns information about available server types and their configuration requirements.

## Troubleshooting

### Connection Test Fails

1. **Check Endpoint URL**: Ensure the URL is correct and accessible
2. **Verify Credentials**: Confirm API keys/tokens are valid and not expired
3. **Network Connectivity**: Ensure FlowGate can reach the server endpoint
4. **Authentication**: Verify authentication type and configuration match the server requirements

### Resource Discovery Returns Empty

1. **Permissions**: Ensure credentials have necessary permissions to list resources
2. **Server Support**: Verify the server supports MCP resource discovery
3. **API Version**: Check if the server API version is compatible

### AWS Connection Issues

1. **Region**: Verify the specified region is correct
2. **Credentials**: Ensure access keys have appropriate IAM permissions
3. **STS Access**: Confirm credentials can call AWS STS GetCallerIdentity

### GCP Connection Issues

1. **Service Account Key**: Verify the JSON key is valid and not corrupted
2. **Project ID**: Ensure project ID matches the service account
3. **Permissions**: Confirm service account has required GCP permissions

### Grafana Connection Issues

1. **API Token**: Verify the Grafana API token is valid
2. **Token Permissions**: Ensure token has necessary permissions (Admin, Editor, or Viewer)
3. **URL**: Confirm Grafana URL is accessible and includes protocol (http/https)

## Integration with Other Features

MCP servers configured in the catalog can be used by:

- **Templates**: Reference MCP servers in template configurations
- **Deployments**: Use MCP servers for telemetry export destinations
- **AI Features**: Access external data sources via MCP protocol

## Additional Resources

- [Grafana API Documentation](https://grafana.com/docs/grafana/latest/developers/http_api/)
- [AWS SDK Documentation](https://docs.aws.amazon.com/sdk-for-python/)
- [GCP Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

