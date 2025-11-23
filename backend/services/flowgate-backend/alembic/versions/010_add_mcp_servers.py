"""Add MCP servers table

Revision ID: 010_add_mcp_servers
Revises: 009_add_ai_provider_config
Create Date: 2025-11-23 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_add_mcp_servers'
down_revision = '009_add_ai_provider_config'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types (only if they don't exist)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE mcp_server_type AS ENUM ('grafana', 'aws', 'gcp', 'custom');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE mcp_auth_type AS ENUM ('oauth', 'custom_header', 'no_auth');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE mcp_scope AS ENUM ('personal', 'tenant');
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
            AND table_name = 'mcp_servers'
        );
    """))
    table_exists = result.scalar()
    
    if not table_exists:
        # Create mcp_servers table using raw SQL to avoid enum creation issues
        op.execute("""
            CREATE TABLE mcp_servers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                org_id UUID NOT NULL,
                server_type mcp_server_type NOT NULL,
                server_name VARCHAR(255) NOT NULL,
                endpoint_url VARCHAR(512),
                auth_type mcp_auth_type NOT NULL DEFAULT 'no_auth',
                auth_config JSONB,
                scope mcp_scope NOT NULL DEFAULT 'personal',
                is_enabled BOOLEAN NOT NULL DEFAULT false,
                is_active BOOLEAN NOT NULL DEFAULT false,
                last_tested_at TIMESTAMP WITH TIME ZONE,
                last_test_status VARCHAR(50),
                last_test_error VARCHAR(512),
                discovered_resources JSONB,
                server_metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE,
                CONSTRAINT fk_mcp_servers_org_id FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE
            );
        """)
        
        # Create indexes
        op.create_index('ix_mcp_servers_org_id', 'mcp_servers', ['org_id'])
        op.create_index('ix_mcp_servers_server_type', 'mcp_servers', ['server_type'])
        op.create_index('ix_mcp_servers_is_enabled', 'mcp_servers', ['is_enabled'])


def downgrade() -> None:
    op.drop_index('ix_mcp_servers_is_enabled', table_name='mcp_servers')
    op.drop_index('ix_mcp_servers_server_type', table_name='mcp_servers')
    op.drop_index('ix_mcp_servers_org_id', table_name='mcp_servers')
    op.drop_table('mcp_servers')
    op.execute("DROP TYPE mcp_scope")
    op.execute("DROP TYPE mcp_auth_type")
    op.execute("DROP TYPE mcp_server_type")

