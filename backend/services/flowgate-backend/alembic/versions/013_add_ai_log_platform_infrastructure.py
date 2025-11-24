"""Add AI Log Platform infrastructure

Revision ID: 013_add_ai_log_platform_infrastructure
Revises: 012_add_additional_log_formats
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_add_ai_log_platform_infrastructure'
down_revision = '012_add_additional_log_formats'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Note: Actual tables for AI log platform will be added in subsequent migrations
    # This migration only sets up the infrastructure (pgvector extension)


def downgrade() -> None:
    # Drop pgvector extension (be careful - this will remove all vector columns)
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE;")

