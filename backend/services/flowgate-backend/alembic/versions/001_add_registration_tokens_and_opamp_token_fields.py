"""add registration tokens and opamp token fields

Revision ID: 001_registration_tokens
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_registration_tokens'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create registration_tokens table
    op.create_table(
        'registration_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_registration_tokens_token'), 'registration_tokens', ['token'], unique=True)
    op.create_index(op.f('ix_registration_tokens_org_id'), 'registration_tokens', ['org_id'], unique=False)
    
    # Add opamp_token and registration_token_id to gateways table
    op.add_column('gateways', sa.Column('opamp_token', sa.String(length=512), nullable=True))
    op.add_column('gateways', sa.Column('registration_token_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_gateways_registration_token_id', 'gateways', 'registration_tokens', ['registration_token_id'], ['id'])


def downgrade() -> None:
    # Remove columns from gateways table
    op.drop_constraint('fk_gateways_registration_token_id', 'gateways', type_='foreignkey')
    op.drop_column('gateways', 'registration_token_id')
    op.drop_column('gateways', 'opamp_token')
    
    # Drop registration_tokens table
    op.drop_index(op.f('ix_registration_tokens_org_id'), table_name='registration_tokens')
    op.drop_index(op.f('ix_registration_tokens_token'), table_name='registration_tokens')
    op.drop_table('registration_tokens')

