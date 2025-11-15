"""Add OpAMP config management tables

Revision ID: 003_add_opamp_config_management
Revises: 002_add_opamp_status_fields
Create Date: 2025-11-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_opamp_config_management'
down_revision = '002_add_opamp_status_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create config deployment status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE opamp_config_deployment_status AS ENUM (
                'pending',
                'in_progress',
                'completed',
                'failed',
                'rolled_back'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create config audit status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE opamp_config_audit_status AS ENUM (
                'pending',
                'applying',
                'applied',
                'failed'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create global config version sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS global_config_version_seq START 1")
    
    # Create agent_tags table
    op.create_table(
        'agent_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('gateway_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('gateways.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tag', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.UniqueConstraint('gateway_id', 'tag', name='uq_agent_tag')
    )
    op.create_index('ix_agent_tags_tag', 'agent_tags', ['tag'])
    
    # Create opamp_config_deployments table
    op.create_table(
        'opamp_config_deployments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('config_version', sa.Integer, nullable=False, unique=True, index=True),  # Global version
        sa.Column('config_yaml', sa.Text, nullable=False),
        sa.Column('config_hash', sa.String(256), nullable=False, index=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('templates.id'), nullable=True),
        sa.Column('template_version', sa.Integer, nullable=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False, index=True),
        sa.Column('rollout_strategy', sa.String(50), nullable=False, default='immediate'),
        sa.Column('canary_percentage', sa.Integer, nullable=True),
        sa.Column('target_tags', postgresql.JSONB, nullable=True),  # Array of tag names
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'failed', 'rolled_back', name='opamp_config_deployment_status', create_type=False), nullable=False, default='pending'),
        sa.Column('ignore_failures', sa.Boolean, nullable=False, default=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Create opamp_config_audit table
    op.create_table(
        'opamp_config_audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('deployment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('opamp_config_deployments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('gateway_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('gateways.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('config_version', sa.Integer, nullable=False, index=True),
        sa.Column('config_hash', sa.String(256), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'applying', 'applied', 'failed', name='opamp_config_audit_status', create_type=False), nullable=False),
        sa.Column('status_reported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('effective_config_hash', sa.String(256), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('deployment_id', 'gateway_id', name='uq_audit_deployment_gateway')
    )
    
    # Add columns to gateways table
    op.add_column('gateways', sa.Column('tags', postgresql.JSONB, nullable=True))  # Array of tag strings
    op.add_column('gateways', sa.Column('last_config_deployment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('opamp_config_deployments.id'), nullable=True))
    op.add_column('gateways', sa.Column('last_config_version', sa.Integer, nullable=True))
    op.add_column('gateways', sa.Column('last_config_status', postgresql.ENUM('UNSET', 'APPLIED', 'APPLYING', 'FAILED', name='opamp_remote_config_status', create_type=False), nullable=True))
    op.add_column('gateways', sa.Column('last_config_status_at', sa.DateTime(timezone=True), nullable=True))
    
    op.create_index('ix_gateways_tags', 'gateways', ['tags'], postgresql_using='gin')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_gateways_tags', table_name='gateways')
    
    # Drop columns from gateways
    op.drop_column('gateways', 'last_config_status_at')
    op.drop_column('gateways', 'last_config_status')
    op.drop_column('gateways', 'last_config_version')
    op.drop_column('gateways', 'last_config_deployment_id')
    op.drop_column('gateways', 'tags')
    
    # Drop tables
    op.drop_table('opamp_config_audit')
    op.drop_table('opamp_config_deployments')
    op.drop_table('agent_tags')
    
    # Drop sequence
    op.execute('DROP SEQUENCE IF EXISTS global_config_version_seq')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS opamp_config_audit_status')
    op.execute('DROP TYPE IF EXISTS opamp_config_deployment_status')

