"""Add config_requests and system_templates tables

Revision ID: 007_config_requests_system_templates
Revises: 2d334abc687e
Create Date: 2025-01-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_config_requests_system_templates'
down_revision = '2d334abc687e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create config_request_status enum
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
    
    # Create config_requests table
    op.create_table(
        'config_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tracking_id', sa.String(36), nullable=False, unique=True),
        sa.Column('instance_id', sa.String(255), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'completed', 'failed', name='configrequeststatus'), nullable=False, server_default='pending'),
        sa.Column('effective_config_content', sa.Text(), nullable=True),
        sa.Column('effective_config_hash', sa.String(255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.Index('ix_config_requests_tracking_id', 'tracking_id'),
        sa.Index('ix_config_requests_instance_id', 'instance_id'),
        sa.Index('ix_config_requests_status', 'status'),
        sa.Index('ix_config_requests_org_id', 'org_id'),
        comment='Tracks effective config retrieval requests with tracking IDs'
    )
    
    # Create system_templates table
    op.create_table(
        'system_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config_yaml', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        comment='System templates for default collector configurations'
    )
    
    # Initialize default system template from file
    # Note: This will be done by the service on first access if file exists
    # We just create the table structure here


def downgrade() -> None:
    op.drop_table('system_templates')
    op.drop_table('config_requests')
    op.execute("DROP TYPE IF EXISTS configrequeststatus")

