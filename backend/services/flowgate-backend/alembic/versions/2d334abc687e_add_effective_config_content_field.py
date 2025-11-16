"""add_effective_config_content_field

Revision ID: 2d334abc687e
Revises: 006_opamp_packages_conn_settings
Create Date: 2025-11-16 02:03:41.268252

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d334abc687e'
down_revision = '006_opamp_packages_conn_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column to store effective config YAML content from OpAMP messages
    # This allows us to retrieve the actual config the agent is running,
    # not just the hash
    op.add_column('gateways', sa.Column('opamp_effective_config_content', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('gateways', 'opamp_effective_config_content')
