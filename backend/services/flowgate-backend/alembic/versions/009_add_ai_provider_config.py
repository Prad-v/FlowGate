"""Add AI provider config to settings

Revision ID: 009_add_ai_provider_config
Revises: 008_template_default_version
Create Date: 2025-01-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_ai_provider_config'
down_revision = '008_template_default_version'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add ai_provider_config JSONB column to settings table
    op.add_column(
        'settings',
        sa.Column('ai_provider_config', postgresql.JSONB, nullable=True)
    )


def downgrade() -> None:
    op.drop_column('settings', 'ai_provider_config')

