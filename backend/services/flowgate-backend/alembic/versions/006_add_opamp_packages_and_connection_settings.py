"""Add OpAMP packages and connection settings tables

Revision ID: 006_add_opamp_packages_and_connection_settings
Revises: 005_add_settings_table
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_opamp_packages_conn_settings'
down_revision = '005_add_settings_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create package_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE packagestatus AS ENUM (
                'installed',
                'installing',
                'failed',
                'uninstalled'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create package_type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE packagetype AS ENUM (
                'top_level',
                'addon'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create connection_settings_type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE connectionsettingstype AS ENUM (
                'opamp',
                'own_metrics',
                'own_traces',
                'own_logs',
                'other'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create connection_settings_status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE connectionsettingsstatus AS ENUM (
                'UNSET',
                'APPLIED',
                'APPLYING',
                'FAILED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create agent_packages table
    op.create_table(
        'agent_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gateway_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('package_name', sa.String(255), nullable=False),
        sa.Column('package_version', sa.String(100), nullable=True),
        sa.Column('package_type', postgresql.ENUM('top_level', 'addon', name='packagetype', create_type=False), nullable=False, server_default='top_level'),
        sa.Column('package_hash', sa.String(256), nullable=True),
        sa.Column('status', postgresql.ENUM('installed', 'installing', 'failed', 'uninstalled', name='packagestatus', create_type=False), nullable=False, server_default='uninstalled'),
        sa.Column('installed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(512), nullable=True),
        sa.Column('server_offered_hash', sa.String(256), nullable=True),
        sa.Column('agent_reported_hash', sa.String(256), nullable=True),
        sa.Column('download_url', sa.String(512), nullable=True),
        sa.Column('content_hash', sa.String(256), nullable=True),
        sa.Column('signature', postgresql.BYTEA, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['gateway_id'], ['gateways.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_packages_gateway_id'), 'agent_packages', ['gateway_id'], unique=False)
    op.create_index(op.f('ix_agent_packages_org_id'), 'agent_packages', ['org_id'], unique=False)
    
    # Create connection_settings table
    op.create_table(
        'connection_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gateway_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('settings_type', postgresql.ENUM('opamp', 'own_metrics', 'own_traces', 'own_logs', 'other', name='connectionsettingstype', create_type=False), nullable=False),
        sa.Column('settings_name', sa.String(255), nullable=True),
        sa.Column('settings_hash', sa.String(256), nullable=True),
        sa.Column('status', postgresql.ENUM('UNSET', 'APPLIED', 'APPLYING', 'FAILED', name='connectionsettingsstatus', create_type=False), nullable=False, server_default='UNSET'),
        sa.Column('settings_data', postgresql.JSONB, nullable=True),
        sa.Column('certificate_pem', sa.Text(), nullable=True),
        sa.Column('private_key_pem', sa.Text(), nullable=True),
        sa.Column('ca_cert_pem', sa.Text(), nullable=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(512), nullable=True),
        sa.Column('csr_pem', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['gateway_id'], ['gateways.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_connection_settings_gateway_id'), 'connection_settings', ['gateway_id'], unique=False)
    op.create_index(op.f('ix_connection_settings_org_id'), 'connection_settings', ['org_id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_connection_settings_org_id'), table_name='connection_settings')
    op.drop_index(op.f('ix_connection_settings_gateway_id'), table_name='connection_settings')
    op.drop_table('connection_settings')
    
    op.drop_index(op.f('ix_agent_packages_org_id'), table_name='agent_packages')
    op.drop_index(op.f('ix_agent_packages_gateway_id'), table_name='agent_packages')
    op.drop_table('agent_packages')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS connectionsettingsstatus")
    op.execute("DROP TYPE IF EXISTS connectionsettingstype")
    op.execute("DROP TYPE IF EXISTS packagetype")
    op.execute("DROP TYPE IF EXISTS packagestatus")

