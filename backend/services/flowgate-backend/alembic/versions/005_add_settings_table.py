"""Add settings table

Revision ID: 005_add_settings_table
Revises: 004_add_supervisor_support
Create Date: 2025-11-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_settings_table'
down_revision = '004_add_supervisor_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create settings table
    op.create_table(
        'settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gateway_management_mode', sa.String(20), nullable=False, server_default='supervisor'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id')
    )
    op.create_index(op.f('ix_settings_org_id'), 'settings', ['org_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_settings_org_id'), table_name='settings')
    op.drop_table('settings')

