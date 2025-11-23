"""Add log format templates table

Revision ID: 011_add_log_format_templates
Revises: 010_add_mcp_servers
Create Date: 2025-11-23 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json

# revision identifiers, used by Alembic.
revision = '011_add_log_format_templates'
down_revision = '010_add_mcp_servers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type (only if it doesn't exist)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE log_format_type AS ENUM ('source', 'destination', 'both');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Check if table already exists
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'log_format_templates'
        );
    """))
    table_exists = result.scalar()
    
    if not table_exists:
        # Create log_format_templates table using raw SQL
        op.execute("""
            CREATE TABLE log_format_templates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                format_name VARCHAR(100) NOT NULL UNIQUE,
                display_name VARCHAR(255) NOT NULL,
                format_type log_format_type NOT NULL,
                description TEXT,
                sample_logs TEXT,
                parser_config JSONB,
                schema JSONB,
                is_system_template BOOLEAN NOT NULL DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """)
        
        # Create indexes
        op.create_index('ix_log_format_templates_format_name', 'log_format_templates', ['format_name'])
        op.create_index('ix_log_format_templates_format_type', 'log_format_templates', ['format_type'])
        
        # Insert default system templates using proper JSON escaping
        templates = [
            {
                'format_name': 'nginx',
                'display_name': 'Nginx Access Log',
                'format_type': 'source',
                'description': 'Nginx access log in common or combined format',
                'sample_logs': '127.0.0.1 - - [02/Jan/2024:10:30:45 +0000] "GET /api/users HTTP/1.1" 200 1234 "-" "Mozilla/5.0"',
                'parser_config': {"type": "regex", "regex": r"^(?P<remote_addr>\S+) - (?P<remote_user>\S+) \[(?P<time_local>[^\]]+)\] \"(?P<request>\S+ \S+ \S+)\" (?P<status>\d+) (?P<body_bytes_sent>\d+) \"(?P<http_referer>[^\"]+)\" \"(?P<http_user_agent>[^\"]+)\"$"},
                'schema': {"fields": ["remote_addr", "remote_user", "time_local", "request", "status", "body_bytes_sent", "http_referer", "http_user_agent"]},
            },
            {
                'format_name': 'syslog',
                'display_name': 'Syslog',
                'format_type': 'source',
                'description': 'Syslog format (RFC 3164 or RFC 5424)',
                'sample_logs': '<34>1 2024-01-02T10:30:45.123Z mymachine.example.com su - ID47 - BOM\'su root\' failed for lonvick on /dev/pts/8',
                'parser_config': {"type": "syslog"},
                'schema': {"fields": ["timestamp", "hostname", "appname", "procid", "msgid", "structured_data", "message"]},
            },
            {
                'format_name': 'apache',
                'display_name': 'Apache Access Log',
                'format_type': 'source',
                'description': 'Apache HTTP server access log',
                'sample_logs': '127.0.0.1 - - [02/Jan/2024:10:30:45 +0000] "GET /index.html HTTP/1.1" 200 2326',
                'parser_config': {"type": "regex", "regex": r"^(?P<remote_host>\S+) (?P<remote_logname>\S+) (?P<remote_user>\S+) \[(?P<time>[^\]]+)\] \"(?P<request>\S+ \S+ \S+)\" (?P<status>\d+) (?P<size>\d+)$"},
                'schema': {"fields": ["remote_host", "remote_logname", "remote_user", "time", "request", "status", "size"]},
            },
            {
                'format_name': 'json',
                'display_name': 'JSON Logs',
                'format_type': 'both',
                'description': 'Structured JSON log format',
                'sample_logs': '{"timestamp": "2024-01-02T10:30:45Z", "level": "INFO", "message": "User logged in", "user_id": 12345}',
                'parser_config': {"type": "json"},
                'schema': {"fields": ["timestamp", "level", "message", "user_id"]},
            },
            {
                'format_name': 'csv',
                'display_name': 'CSV Logs',
                'format_type': 'source',
                'description': 'Comma-separated values log format',
                'sample_logs': '2024-01-02,10:30:45,INFO,User logged in,12345',
                'parser_config': {"type": "csv", "delimiter": ",", "headers": ["date", "time", "level", "message", "user_id"]},
                'schema': {"fields": ["date", "time", "level", "message", "user_id"]},
            },
            {
                'format_name': 'log4j',
                'display_name': 'Log4j',
                'format_type': 'source',
                'description': 'Apache Log4j logging format',
                'sample_logs': '2024-01-02 10:30:45,123 [main] INFO  com.example.App - User logged in',
                'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[(?P<thread>\S+)\] (?P<level>\S+)  (?P<logger>\S+) - (?P<message>.*)$"},
                'schema': {"fields": ["timestamp", "thread", "level", "logger", "message"]},
            },
            {
                'format_name': 'docker',
                'display_name': 'Docker Logs',
                'format_type': 'source',
                'description': 'Docker container log format',
                'sample_logs': '2024-01-02T10:30:45.123456789Z stdout F {"message":"User logged in","level":"INFO"}',
                'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>[^Z]+Z) (?P<stream>stdout|stderr) [A-Z] (?P<message>.*)$"},
                'schema': {"fields": ["timestamp", "stream", "message"]},
            },
            {
                'format_name': 'kubernetes',
                'display_name': 'Kubernetes Pod Logs',
                'format_type': 'source',
                'description': 'Kubernetes pod log format',
                'sample_logs': '2024-01-02T10:30:45.123456Z stdout F {"timestamp":"2024-01-02T10:30:45Z","level":"INFO","message":"User logged in"}',
                'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>[^Z]+Z) (?P<stream>stdout|stderr) [A-Z] (?P<message>.*)$"},
                'schema': {"fields": ["timestamp", "stream", "message"]},
            },
            {
                'format_name': 'otlp',
                'display_name': 'OpenTelemetry Protocol',
                'format_type': 'destination',
                'description': 'OpenTelemetry Protocol format for structured telemetry',
                'sample_logs': '{"resourceLogs": [{"resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "my-service"}}]}, "scopeLogs": [{"logRecords": [{"timeUnixNano": "1704192645000000000", "body": {"stringValue": "User logged in"}, "severityText": "INFO"}]}]}]}',
                'parser_config': {"type": "otlp"},
                'schema': {"fields": ["resourceLogs", "scopeLogs", "logRecords"]},
            },
            {
                'format_name': 'structured_json',
                'display_name': 'Structured JSON',
                'format_type': 'destination',
                'description': 'Structured JSON output format',
                'sample_logs': '{"timestamp": "2024-01-02T10:30:45Z", "level": "INFO", "message": "User logged in", "attributes": {"user_id": 12345}}',
                'parser_config': {"type": "json"},
                'schema': {"fields": ["timestamp", "level", "message", "attributes"]},
            },
        ]
        
        for template in templates:
            # Properly escape JSON and text for SQL
            parser_config_json = json.dumps(template['parser_config'])
            schema_json = json.dumps(template['schema'])
            sample_logs_escaped = template['sample_logs'].replace("'", "''")
            description_escaped = template['description'].replace("'", "''")
            
            op.execute(f"""
                INSERT INTO log_format_templates (format_name, display_name, format_type, description, sample_logs, parser_config, schema, is_system_template)
                VALUES (
                    '{template["format_name"]}',
                    '{template["display_name"]}',
                    '{template["format_type"]}',
                    '{description_escaped}',
                    '{sample_logs_escaped}',
                    '{parser_config_json}'::jsonb,
                    '{schema_json}'::jsonb,
                    true
                );
            """)


def downgrade() -> None:
    op.drop_index('ix_log_format_templates_format_type', table_name='log_format_templates')
    op.drop_index('ix_log_format_templates_format_name', table_name='log_format_templates')
    op.drop_table('log_format_templates')
    op.execute("DROP TYPE log_format_type")
