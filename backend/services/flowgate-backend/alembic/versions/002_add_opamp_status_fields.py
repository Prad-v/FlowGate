"""Add OpAMP status tracking fields

Revision ID: 002_add_opamp_status_fields
Revises: 001_add_registration_tokens_and_opamp_token_fields
Create Date: 2025-11-14 20:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_opamp_status_fields'
down_revision = '001_registration_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create OpAMP connection status enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE opamp_connection_status AS ENUM (
                'connected',
                'disconnected',
                'failed',
                'never_connected'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create OpAMP remote config status enum (per OpAMP spec)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE opamp_remote_config_status AS ENUM (
                'UNSET',
                'APPLIED',
                'APPLYING',
                'FAILED'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add OpAMP status fields to gateways table
    op.add_column('gateways', sa.Column('opamp_connection_status', 
        postgresql.ENUM('connected', 'disconnected', 'failed', 'never_connected', 
                       name='opamp_connection_status', create_type=False), 
        nullable=True, server_default=sa.text("'never_connected'")))
    
    op.add_column('gateways', sa.Column('opamp_remote_config_status',
        postgresql.ENUM('UNSET', 'APPLIED', 'APPLYING', 'FAILED',
                       name='opamp_remote_config_status', create_type=False),
        nullable=True, server_default=sa.text("'UNSET'")))
    
    op.add_column('gateways', sa.Column('opamp_last_sequence_num', sa.Integer(), nullable=True))
    op.add_column('gateways', sa.Column('opamp_transport_type', sa.String(20), nullable=True))
    op.add_column('gateways', sa.Column('opamp_registration_failed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('gateways', sa.Column('opamp_registration_failure_reason', sa.String(512), nullable=True))
    op.add_column('gateways', sa.Column('opamp_agent_capabilities', sa.BigInteger(), nullable=True))
    op.add_column('gateways', sa.Column('opamp_server_capabilities', sa.BigInteger(), nullable=True))
    op.add_column('gateways', sa.Column('opamp_effective_config_hash', sa.String(256), nullable=True))
    op.add_column('gateways', sa.Column('opamp_remote_config_hash', sa.String(256), nullable=True))


def downgrade() -> None:
    # Remove columns
    op.drop_column('gateways', 'opamp_remote_config_hash')
    op.drop_column('gateways', 'opamp_effective_config_hash')
    op.drop_column('gateways', 'opamp_server_capabilities')
    op.drop_column('gateways', 'opamp_agent_capabilities')
    op.drop_column('gateways', 'opamp_registration_failure_reason')
    op.drop_column('gateways', 'opamp_registration_failed_at')
    op.drop_column('gateways', 'opamp_transport_type')
    op.drop_column('gateways', 'opamp_last_sequence_num')
    op.drop_column('gateways', 'opamp_remote_config_status')
    op.drop_column('gateways', 'opamp_connection_status')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS opamp_remote_config_status')
    op.execute('DROP TYPE IF EXISTS opamp_connection_status')

