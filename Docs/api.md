# Flowgate API Documentation

## Base URL

- Local: `http://localhost:8000/api/v1`
- Production: `https://api.flowgate.com/api/v1`

## Authentication

Currently, authentication is not implemented. In production, use JWT tokens:

```
Authorization: Bearer <token>
```

## Endpoints

### Templates

#### Create Template
```http
POST /templates
Content-Type: application/json

{
  "name": "string",
  "description": "string (optional)",
  "template_type": "metric|log|trace|routing",
  "config_yaml": "string",
  "change_summary": "string (optional)"
}
```

#### List Templates
```http
GET /templates?skip=0&limit=100
```

#### Get Template
```http
GET /templates/{template_id}
```

#### Update Template
```http
PUT /templates/{template_id}
Content-Type: application/json

{
  "name": "string (optional)",
  "description": "string (optional)",
  "is_active": boolean (optional),
  "config_yaml": "string (optional)",
  "change_summary": "string (optional)"
}
```

#### Delete Template
```http
DELETE /templates/{template_id}
```

#### List Template Versions
```http
GET /templates/{template_id}/versions
```

#### Get Template Version
```http
GET /templates/{template_id}/versions/{version}
```

#### Validate Template
```http
POST /templates/validate
Content-Type: application/json

{
  "config_yaml": "string",
  "sample_metrics": [object] (optional),
  "sample_logs": [string] (optional)
}
```

### Deployments

#### Create Deployment
```http
POST /deployments
Content-Type: application/json

{
  "name": "string",
  "template_id": "uuid",
  "template_version": integer,
  "gateway_id": "uuid (optional)",
  "rollout_strategy": "immediate|canary|staged",
  "canary_percentage": integer (optional),
  "metadata": object (optional)
}
```

#### List Deployments
```http
GET /deployments?skip=0&limit=100
```

#### Get Deployment
```http
GET /deployments/{deployment_id}
```

#### Rollback Deployment
```http
POST /deployments/{deployment_id}/rollback
```

### Gateways

#### Register Gateway
```http
POST /gateways
Content-Type: application/json

{
  "name": "string",
  "instance_id": "string",
  "hostname": "string (optional)",
  "ip_address": "string (optional)",
  "version": "string (optional)",
  "metadata": object (optional)
}
```

#### Update Heartbeat
```http
POST /gateways/{instance_id}/heartbeat
Content-Type: application/json

{
  "status": "online|offline|unknown",
  "version": "string (optional)",
  "metadata": object (optional)
}
```

#### List Gateways
```http
GET /gateways?skip=0&limit=100
```

#### Get Gateway
```http
GET /gateways/{gateway_id}
```

#### Update Gateway
```http
PUT /gateways/{gateway_id}
Content-Type: application/json

{
  "name": "string (optional)",
  "status": "online|offline|unknown (optional)",
  "hostname": "string (optional)",
  "ip_address": "string (optional)",
  "version": "string (optional)",
  "config_version": integer (optional),
  "metadata": object (optional)
}
```

### Health

#### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy"
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "detail": "Detailed error description (optional)",
  "code": "ERROR_CODE (optional)"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error


