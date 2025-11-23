"""Add additional log format templates

Revision ID: 012_add_additional_log_formats
Revises: 011_add_log_format_templates
Create Date: 2025-11-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json

# revision identifiers, used by Alembic.
revision = '012_add_additional_log_formats'
down_revision = '011_add_log_format_templates'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Additional log format templates for cloud providers, auth systems, and IT processes
    templates = [
        {
            'format_name': 'google_cloud_auth',
            'display_name': 'Google Cloud Auth Logs',
            'format_type': 'source',
            'description': 'Google Cloud Platform authentication and access logs (Cloud Audit Logs)',
            'sample_logs': '{"insertId":"abc123","logName":"projects/my-project/logs/cloudaudit.googleapis.com%2Fdata_access","protoPayload":{"@type":"type.googleapis.com/google.cloud.audit.AuditLog","authenticationInfo":{"principalEmail":"user@example.com"},"requestMetadata":{"callerIp":"192.168.1.1","callerSuppliedUserAgent":"gcloud/1.0"},"serviceName":"storage.googleapis.com","methodName":"storage.objects.get","resourceName":"projects/_/buckets/my-bucket/objects/file.txt"},"timestamp":"2024-01-02T10:30:45.123Z"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["insertId", "logName", "protoPayload", "timestamp", "severity", "resource"]},
        },
        {
            'format_name': 'aws_cloudtrail',
            'display_name': 'AWS CloudTrail Logs',
            'format_type': 'source',
            'description': 'AWS CloudTrail API audit logs in JSON format',
            'sample_logs': '{"eventVersion":"1.08","userIdentity":{"type":"IAMUser","userName":"john.doe","arn":"arn:aws:iam::123456789012:user/john.doe"},"eventTime":"2024-01-02T10:30:45Z","eventSource":"s3.amazonaws.com","eventName":"GetObject","awsRegion":"us-east-1","sourceIPAddress":"192.168.1.1","userAgent":"aws-cli/2.0","requestParameters":{"bucketName":"my-bucket","key":"file.txt"},"responseElements":null,"requestID":"ABC123","eventID":"def456-789"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["eventVersion", "userIdentity", "eventTime", "eventSource", "eventName", "awsRegion", "sourceIPAddress", "userAgent", "requestParameters", "responseElements"]},
        },
        {
            'format_name': 'azure_audit',
            'display_name': 'Azure Audit Logs',
            'format_type': 'source',
            'description': 'Microsoft Azure Activity and Audit logs in JSON format',
            'sample_logs': '{"time":"2024-01-02T10:30:45.123Z","resourceId":"/subscriptions/123/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/mystorage","operationName":"Microsoft.Storage/storageAccounts/listKeys/action","category":"Administrative","resultType":"Success","correlationId":"abc-123-def","caller":"user@example.com","callerIpAddress":"192.168.1.1","properties":{"requestBody":"{}","responseBody":"{\\"keys\\":[]}"}}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["time", "resourceId", "operationName", "category", "resultType", "correlationId", "caller", "callerIpAddress", "properties"]},
        },
        {
            'format_name': 'oci_audit',
            'display_name': 'Oracle Cloud Infrastructure Audit Logs',
            'format_type': 'source',
            'description': 'OCI Audit service logs in JSON format',
            'sample_logs': '{"eventType":"com.oraclecloud.objectstorage.createobject","cloudEventsVersion":"0.1","eventTypeVersion":"2.0","source":"objectstorage","eventId":"ocid1.event.abc123","eventTime":"2024-01-02T10:30:45.123Z","contentType":"application/json","data":{"compartmentId":"ocid1.compartment.abc123","compartmentName":"my-compartment","resourceName":"my-bucket/file.txt","resourceId":"ocid1.bucket.abc123","availabilityDomain":"us-ashburn-1","freeformTags":{},"definedTags":{}}}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["eventType", "cloudEventsVersion", "source", "eventId", "eventTime", "data"]},
        },
        {
            'format_name': 'active_directory',
            'display_name': 'Active Directory Logs',
            'format_type': 'source',
            'description': 'Windows Active Directory security and authentication logs (Event ID 4624, 4625, etc.)',
            'sample_logs': '2024-01-02 10:30:45,123 Security 4624 An account was successfully logged on. Subject: Security ID: S-1-5-18 Account Name: SYSTEM Account Domain: NT AUTHORITY Logon ID: 0x3e7 Logon Type: 3 New Logon: Security ID: S-1-5-21-1234567890-123456789-123456789-1234 Account Name: john.doe Account Domain: EXAMPLE Process Information: Process ID: 0x1234 Process Name: C:\\Windows\\System32\\lsass.exe Network Information: Workstation Name: WORKSTATION-01 Source Network Address: 192.168.1.100 Source Port: 12345',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<log_type>\w+)\s+(?P<event_id>\d+)\s+(?P<message>.*)$"},
            'schema': {"fields": ["timestamp", "log_type", "event_id", "message", "account_name", "domain", "source_ip", "logon_type"]},
        },
        {
            'format_name': 'okta_auth',
            'display_name': 'Okta Authentication Logs',
            'format_type': 'source',
            'description': 'Okta System Log authentication and authorization events in JSON format',
            'sample_logs': '{"actor":{"id":"00u1abc2def3ghi4jkl","type":"User","alternateId":"user@example.com","displayName":"John Doe"},"client":{"userAgent":{"rawUserAgent":"Mozilla/5.0","os":"Mac OS X","browser":"CHROME"},"ipAddress":"192.168.1.100","geographicalContext":{"city":"San Francisco","state":"California","country":"United States"}},"authenticationContext":{"authenticationProvider":"OKTA_AUTHENTICATION_PROVIDER","credentialProvider":"OKTA_CREDENTIAL_PROVIDER","credentialType":"PASSWORD","issuer":{"type":"Org","id":"00o1abc2def3ghi4jkl"},"externalSessionId":"102abc3def4ghi5jkl"},"displayMessage":"User login to Okta","eventType":"user.authentication.sso","outcome":{"result":"SUCCESS","reason":null},"published":"2024-01-02T10:30:45.123Z","request":{"ipChain":[{"ip":"192.168.1.100","geographicalContext":{"city":"San Francisco","state":"California","country":"United States"}}]},"securityContext":{"asNumber":null,"asOrg":null,"domain":"example.com","isProxy":null},"severity":"INFO","target":[],"uuid":"abc123-def456-ghi789","version":"0"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["actor", "client", "authenticationContext", "displayMessage", "eventType", "outcome", "published", "request", "severity"]},
        },
        {
            'format_name': 'splunk',
            'display_name': 'Splunk Logs',
            'format_type': 'source',
            'description': 'Splunk search results and indexed log format',
            'sample_logs': '2024-01-02 10:30:45.123 INFO [search] user="admin" action="search" query="index=main *" results=1000 duration_ms=250 source="splunkd" component="SearchManager"',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<message>.*)$"},
            'schema': {"fields": ["timestamp", "level", "component", "message", "user", "action", "query", "results", "duration_ms", "source"]},
        },
        {
            'format_name': 'ldap_auth',
            'display_name': 'LDAP Authentication Logs',
            'format_type': 'source',
            'description': 'LDAP (Lightweight Directory Access Protocol) authentication and access logs',
            'sample_logs': '2024-01-02T10:30:45.123Z conn=1234 op=5678 BIND dn="cn=john.doe,ou=users,dc=example,dc=com" method=128 result=0 msg=""',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>[^\s]+)\s+conn=(?P<connection_id>\d+)\s+op=(?P<operation_id>\d+)\s+(?P<operation>\w+)\s+dn=\"(?P<distinguished_name>[^\"]+)\"\s+method=(?P<method>\d+)\s+result=(?P<result_code>\d+)\s+msg=\"(?P<message>[^\"]*)\"$"},
            'schema': {"fields": ["timestamp", "connection_id", "operation_id", "operation", "distinguished_name", "method", "result_code", "message"]},
        },
        {
            'format_name': 'radius_auth',
            'display_name': 'RADIUS Authentication Logs',
            'format_type': 'source',
            'description': 'RADIUS (Remote Authentication Dial-In User Service) authentication logs',
            'sample_logs': 'Wed Jan  2 10:30:45 2024 : Auth: Login OK: [john.doe] (from client 192.168.1.1 port 1812 cli 192.168.1.100)',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>[A-Za-z]{3} [A-Za-z]{3} [\s\d]{2} \d{2}:\d{2}:\d{2} \d{4})\s+:\s+(?P<event_type>\w+):\s+(?P<status>[^:]+):\s+\[(?P<username>[^\]]+)\]\s+\(from client (?P<client_ip>\S+) port (?P<port>\d+) cli (?P<client_id>\S+)\)$"},
            'schema': {"fields": ["timestamp", "event_type", "status", "username", "client_ip", "port", "client_id"]},
        },
        {
            'format_name': 'kerberos_auth',
            'display_name': 'Kerberos Authentication Logs',
            'format_type': 'source',
            'description': 'Kerberos authentication and ticket granting service logs',
            'sample_logs': '2024-01-02 10:30:45.123 [KRB5KDC_ERR_PREAUTH_REQUIRED] preauthentication failed -- CLIENT: user@EXAMPLE.COM from 192.168.1.100 for krbtgt/EXAMPLE.COM@EXAMPLE.COM, Client \'user@EXAMPLE.COM\' not found in Kerberos database',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+\[(?P<error_code>[^\]]+)\]\s+(?P<message>.*?)\s+--\s+CLIENT:\s+(?P<client>[^\s]+)\s+from\s+(?P<source_ip>\S+)\s+for\s+(?P<service_principal>[^\s,]+).*$"},
            'schema': {"fields": ["timestamp", "error_code", "message", "client", "source_ip", "service_principal"]},
        },
        {
            'format_name': 'saml_auth',
            'display_name': 'SAML Authentication Logs',
            'format_type': 'source',
            'description': 'SAML (Security Assertion Markup Language) authentication and SSO logs',
            'sample_logs': '2024-01-02T10:30:45.123Z INFO [SAML] SSO_LOGIN_SUCCESS user="john.doe@example.com" session_id="sess_abc123" idp="https://idp.example.com/saml" sp="https://sp.example.com/saml" assertion_id="assert_123456"',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>[^\s]+)\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<event>\w+)\s+user=\"(?P<user>[^\"]+)\"\s+session_id=\"(?P<session_id>[^\"]+)\"\s+idp=\"(?P<idp>[^\"]+)\"\s+sp=\"(?P<sp>[^\"]+)\"\s+assertion_id=\"(?P<assertion_id>[^\"]+)\"$"},
            'schema': {"fields": ["timestamp", "level", "component", "event", "user", "session_id", "idp", "sp", "assertion_id"]},
        },
        {
            'format_name': 'oauth_auth',
            'display_name': 'OAuth Authentication Logs',
            'format_type': 'source',
            'description': 'OAuth 2.0 and OpenID Connect authentication logs',
            'sample_logs': '2024-01-02T10:30:45.123Z INFO [OAuth] TOKEN_ISSUED client_id="client_123" user_id="user_456" grant_type="authorization_code" scope="read write" expires_in=3600',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>[^\s]+)\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<event>\w+)\s+client_id=\"(?P<client_id>[^\"]+)\"\s+user_id=\"(?P<user_id>[^\"]+)\"\s+grant_type=\"(?P<grant_type>[^\"]+)\"\s+scope=\"(?P<scope>[^\"]+)\"\s+expires_in=(?P<expires_in>\d+)$"},
            'schema': {"fields": ["timestamp", "level", "component", "event", "client_id", "user_id", "grant_type", "scope", "expires_in"]},
        },
    ]
    
    for template in templates:
        # Check if template already exists
        connection = op.get_bind()
        result = connection.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM log_format_templates 
                WHERE format_name = :format_name
            );
        """), {"format_name": template["format_name"]})
        exists = result.scalar()
        
        if not exists:
            # Properly escape JSON and text for SQL
            parser_config_json = json.dumps(template['parser_config'])
            schema_json = json.dumps(template['schema'])
            
            # Use parameterized query to avoid SQL injection and null issues
            connection.execute(sa.text("""
                INSERT INTO log_format_templates (format_name, display_name, format_type, description, sample_logs, parser_config, schema, is_system_template)
                VALUES (
                    :format_name,
                    :display_name,
                    :format_type,
                    :description,
                    :sample_logs,
                    CAST(:parser_config AS jsonb),
                    CAST(:schema AS jsonb),
                    true
                );
            """), {
                "format_name": template["format_name"],
                "display_name": template["display_name"],
                "format_type": template["format_type"],
                "description": template["description"],
                "sample_logs": template["sample_logs"],
                "parser_config": parser_config_json,
                "schema": schema_json,
            })
            connection.commit()


def downgrade() -> None:
    # Remove the additional log format templates
    op.execute("""
        DELETE FROM log_format_templates 
        WHERE format_name IN (
            'google_cloud_auth', 'aws_cloudtrail', 'azure_audit', 'oci_audit',
            'active_directory', 'okta_auth', 'splunk', 'ldap_auth',
            'radius_auth', 'kerberos_auth', 'saml_auth', 'oauth_auth'
        );
    """)

