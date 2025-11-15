"""Add supervisor support fields

Revision ID: 004_add_supervisor_support
Revises: 003_add_opamp_config_management
Create Date: 2025-11-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_supervisor_support'
down_revision = '003_add_opamp_config_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create management_mode enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE management_mode AS ENUM (
                'extension',
                'supervisor'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add supervisor support columns to gateways table
    op.add_column('gateways', sa.Column('management_mode', postgresql.ENUM('extension', 'supervisor', name='management_mode', create_type=False), server_default='extension', nullable=False))
    op.add_column('gateways', sa.Column('supervisor_status', postgresql.JSONB, nullable=True))
    op.add_column('gateways', sa.Column('supervisor_logs_path', sa.String(512), nullable=True))


def downgrade() -> None:
    # Remove supervisor support columns
    op.drop_column('gateways', 'supervisor_logs_path')
    op.drop_column('gateways', 'supervisor_status')
    op.drop_column('gateways', 'management_mode')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS management_mode")

