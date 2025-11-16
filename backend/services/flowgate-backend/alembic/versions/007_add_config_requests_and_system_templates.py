"""Add config_requests and system_templates tables

Revision ID: 007_config_requests_system_templates
Revises: 2d334abc687e
Create Date: 2025-01-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_cfg_req_sys_tmpl'
down_revision = '2d334abc687e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create config_request_status enum (if it doesn't exist)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE configrequeststatus AS ENUM (
                'pending',
                'completed',
                'failed'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create config_requests table (if it doesn't exist)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'config_requests') THEN
                CREATE TABLE config_requests (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tracking_id VARCHAR(36) NOT NULL UNIQUE,
                    instance_id VARCHAR(255) NOT NULL,
                    org_id UUID NOT NULL REFERENCES organizations(id),
                    status configrequeststatus NOT NULL DEFAULT 'pending',
                    effective_config_content TEXT,
                    effective_config_hash VARCHAR(255),
                    error_message TEXT,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
                );
                CREATE INDEX ix_config_requests_tracking_id ON config_requests(tracking_id);
                CREATE INDEX ix_config_requests_instance_id ON config_requests(instance_id);
                CREATE INDEX ix_config_requests_status ON config_requests(status);
                CREATE INDEX ix_config_requests_org_id ON config_requests(org_id);
                COMMENT ON TABLE config_requests IS 'Tracks effective config retrieval requests with tracking IDs';
            END IF;
        END $$;
    """)
    
    # Create system_templates table (if it doesn't exist)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'system_templates') THEN
                CREATE TABLE system_templates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT,
                    config_yaml TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
                );
                COMMENT ON TABLE system_templates IS 'System templates for default collector configurations';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS system_templates")
    op.execute("DROP TABLE IF EXISTS config_requests")
    op.execute("DROP TYPE IF EXISTS configrequeststatus")
