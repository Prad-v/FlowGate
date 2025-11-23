# Log Transformer Studio

The Log Transformer Studio provides AI-assisted transformation of unstructured logs into structured formats using OpenTelemetry Collector configurations.

## Overview

The Log Transformer Studio allows you to:
- Select source and destination log formats from predefined templates
- Get AI-based recommendations for optimal destination formats
- Generate OpenTelemetry transform processor configurations
- Validate and test transformations with dry-run functionality

## Features

### Format Templates

Predefined log format templates are available for common log formats:

**Source Formats:**
- **Nginx Access Log**: Common and combined log formats
- **Syslog**: RFC 3164 and RFC 5424 formats
- **Apache Access Log**: Common, combined, and custom formats
- **JSON**: Structured JSON logs
- **CSV**: Comma-separated values
- **Log4j**: Apache Log4j logging format
- **Docker**: Docker container logs
- **Kubernetes**: Kubernetes pod logs

**Cloud Provider Auth Logs:**
- **Google Cloud Auth Logs**: GCP Cloud Audit Logs (authentication and access)
- **AWS CloudTrail Logs**: AWS API audit logs in JSON format
- **Azure Audit Logs**: Microsoft Azure Activity and Audit logs
- **Oracle Cloud Infrastructure (OCI) Audit Logs**: OCI Audit service logs

**Authentication & Identity Logs:**
- **Active Directory Logs**: Windows AD security and authentication logs (Event ID 4624, 4625, etc.)
- **Okta Authentication Logs**: Okta System Log authentication and authorization events
- **LDAP Authentication Logs**: LDAP authentication and access logs
- **RADIUS Authentication Logs**: RADIUS authentication logs
- **Kerberos Authentication Logs**: Kerberos authentication and ticket granting service logs
- **SAML Authentication Logs**: SAML authentication and SSO logs
- **OAuth Authentication Logs**: OAuth 2.0 and OpenID Connect authentication logs

**IT Process Logs:**
- **Splunk Logs**: Splunk search results and indexed log format

**Destination Formats:**
- **Structured JSON**: Standard structured JSON output
- **OpenTelemetry Protocol (OTLP)**: OTLP format for observability pipelines

### AI Recommendations

The system provides AI-based recommendations for destination formats based on:
- Source format characteristics
- Sample log structure analysis
- Intended use case (monitoring, analytics, compliance)
- Format compatibility

### Transformation Generation

The AI-powered transformation engine:
- Analyzes source and destination formats
- Generates OpenTelemetry transform processor configurations
- Includes parser configurations for source formats
- Creates transformation rules based on target JSON structure

## Usage

### Basic Workflow

1. **Select Source Format**: Choose the format of your input logs from the source format dropdown
2. **Get Recommendations** (Optional): Click "Get Recommendations" to see AI-suggested destination formats
3. **Select Destination Format**: Choose the desired output format
4. **Enter Sample Logs**: Paste sample log entries in the input panel
5. **Define Target Structure** (Optional): Specify the desired JSON structure in the target panel
6. **Generate Config**: Click "Generate Config" to create the OTel configuration
7. **Validate**: Use "Validate Config" to check syntax and configuration
8. **Dry Run**: Test the transformation with "Dry Run" to see actual output

### Format Selection

When selecting a format, you'll see:
- Format description
- Sample log entries
- Expected schema/structure
- Parser configuration details

### AI Recommendations

The recommendation system analyzes:
- Source format characteristics
- Log structure (timestamps, structured data, JSON content)
- Use case requirements
- Format compatibility

Recommendations include:
- Confidence scores (0-100%)
- Compatibility scores
- Reasoning for each recommendation

### Generated Configuration

The generated OTel config includes:
- Transform processor configuration
- Parser settings for source format
- Transformation rules
- Attribute mappings

## API Reference

### List Format Templates

```http
GET /api/v1/log-transformer/formats?format_type=source
```

Query Parameters:
- `format_type` (optional): Filter by "source", "destination", or "both"

### Get Format Template

```http
GET /api/v1/log-transformer/formats/{format_name}
```

### Transform Logs

```http
POST /api/v1/log-transformer/transform
Content-Type: application/json

{
  "source_format": "nginx",
  "destination_format": "structured_json",
  "sample_logs": "127.0.0.1 - - [02/Jan/2024:10:30:45 +0000] \"GET /api/users HTTP/1.1\" 200 1234",
  "target_json": "{\"level\": \"INFO\", \"status\": 200}"
}
```

### Get Recommendations

```http
POST /api/v1/log-transformer/recommend
Content-Type: application/json

{
  "source_format": "nginx",
  "sample_logs": "...",
  "use_case": "monitoring"
}
```

### Validate Config

```http
POST /api/v1/log-transformer/validate
Content-Type: application/json

{
  "config": "processors:\n  transform:\n    ...",
  "sample_logs": "..."
}
```

### Dry Run

```http
POST /api/v1/log-transformer/dry-run
Content-Type: application/json

{
  "config": "processors:\n  transform:\n    ...",
  "sample_logs": "..."
}
```

## Format-Specific Guides

### Nginx Access Log

**Common Format:**
```
127.0.0.1 - - [02/Jan/2024:10:30:45 +0000] "GET /api/users HTTP/1.1" 200 1234
```

**Fields:**
- `remote_addr`: Client IP address
- `remote_user`: Remote user (usually "-")
- `time_local`: Request timestamp
- `request`: HTTP request line
- `status`: HTTP status code
- `body_bytes_sent`: Response body size
- `http_referer`: Referer header
- `http_user_agent`: User agent string

### Syslog

**RFC 3164 Format:**
```
<34>Jan  2 10:30:45 mymachine su: 'su root' failed for lonvick on /dev/pts/8
```

**RFC 5424 Format:**
```
<34>1 2024-01-02T10:30:45.123Z mymachine.example.com su - ID47 - BOM'su root' failed
```

**Fields:**
- `timestamp`: Log timestamp
- `hostname`: Source hostname
- `appname`: Application name
- `procid`: Process ID
- `msgid`: Message ID
- `message`: Log message

### JSON Logs

**Format:**
```json
{
  "timestamp": "2024-01-02T10:30:45Z",
  "level": "INFO",
  "message": "User logged in",
  "user_id": 12345
}
```

JSON logs are automatically parsed and can be easily transformed to any destination format.

### Cloud Provider Auth Logs

#### AWS CloudTrail
**Format:** JSON
```json
{
  "eventVersion": "1.08",
  "userIdentity": {
    "type": "IAMUser",
    "userName": "john.doe"
  },
  "eventTime": "2024-01-02T10:30:45Z",
  "eventSource": "s3.amazonaws.com",
  "eventName": "GetObject",
  "awsRegion": "us-east-1",
  "sourceIPAddress": "192.168.1.1"
}
```

#### Google Cloud Auth Logs
**Format:** JSON (Cloud Audit Logs)
```json
{
  "insertId": "abc123",
  "logName": "projects/my-project/logs/cloudaudit.googleapis.com%2Fdata_access",
  "protoPayload": {
    "authenticationInfo": {
      "principalEmail": "user@example.com"
    },
    "serviceName": "storage.googleapis.com",
    "methodName": "storage.objects.get"
  },
  "timestamp": "2024-01-02T10:30:45.123Z"
}
```

#### Azure Audit Logs
**Format:** JSON
```json
{
  "time": "2024-01-02T10:30:45.123Z",
  "resourceId": "/subscriptions/123/resourceGroups/rg/...",
  "operationName": "Microsoft.Storage/storageAccounts/listKeys/action",
  "category": "Administrative",
  "resultType": "Success",
  "caller": "user@example.com",
  "callerIpAddress": "192.168.1.1"
}
```

### Authentication System Logs

#### Active Directory
**Format:** Windows Event Log format
```
2024-01-02 10:30:45,123 Security 4624 An account was successfully logged on.
Subject: Security ID: S-1-5-18 Account Name: SYSTEM
New Logon: Security ID: S-1-5-21-... Account Name: john.doe
Network Information: Source Network Address: 192.168.1.100
```

#### Okta Authentication
**Format:** JSON (Okta System Log)
```json
{
  "actor": {
    "type": "User",
    "alternateId": "user@example.com",
    "displayName": "John Doe"
  },
  "client": {
    "ipAddress": "192.168.1.100",
    "geographicalContext": {
      "city": "San Francisco",
      "country": "United States"
    }
  },
  "authenticationContext": {
    "authenticationProvider": "OKTA_AUTHENTICATION_PROVIDER",
    "credentialType": "PASSWORD"
  },
  "displayMessage": "User login to Okta",
  "eventType": "user.authentication.sso",
  "outcome": {
    "result": "SUCCESS"
  },
  "published": "2024-01-02T10:30:45.123Z"
}
```

#### LDAP Authentication
**Format:** LDAP access log format
```
2024-01-02T10:30:45.123Z conn=1234 op=5678 BIND 
dn="cn=john.doe,ou=users,dc=example,dc=com" 
method=128 result=0 msg=""
```

#### SAML Authentication
**Format:** Structured log format
```
2024-01-02T10:30:45.123Z INFO [SAML] SSO_LOGIN_SUCCESS 
user="john.doe@example.com" session_id="sess_abc123" 
idp="https://idp.example.com/saml" 
sp="https://sp.example.com/saml"
```

#### OAuth Authentication
**Format:** Structured log format
```
2024-01-02T10:30:45.123Z INFO [OAuth] TOKEN_ISSUED 
client_id="client_123" user_id="user_456" 
grant_type="authorization_code" scope="read write" expires_in=3600
```

## Best Practices

1. **Provide Representative Samples**: Include multiple log entries that represent different scenarios
2. **Specify Target Structure**: Define the desired JSON structure for better transformation accuracy
3. **Use Recommendations**: Leverage AI recommendations for optimal format selection
4. **Validate Before Deploying**: Always validate and dry-run configurations before deployment
5. **Test with Real Data**: Use actual log samples to ensure transformations work correctly

## Troubleshooting

### No Recommendations Available

- Ensure AI provider is configured in Settings
- Check that sample logs are provided
- Verify source format is selected

### Generation Fails

- Check that sample logs are provided
- Verify AI provider is active and configured
- Review error messages for specific issues

### Validation Errors

- Check YAML syntax
- Verify processor names are correct
- Ensure required fields are present

## Additional Resources

- [OpenTelemetry Transform Processor Documentation](https://opentelemetry.io/docs/collector/processors/transform/)
- [OpenTelemetry Collector Configuration Guide](https://opentelemetry.io/docs/collector/configuration/)
- [Log Format Standards](https://en.wikipedia.org/wiki/Common_Log_Format)

