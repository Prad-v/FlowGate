"""Add template default_version_id and system template support

Revision ID: 008_template_default_version
Revises: 007_cfg_req_sys_tmpl
Create Date: 2025-01-16 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_template_default_version'
down_revision = '007_cfg_req_sys_tmpl'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make org_id nullable for system templates
    op.alter_column('templates', 'org_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True,
                    existing_nullable=False)
    
    # Add is_system_template column
    op.add_column('templates',
                  sa.Column('is_system_template', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add default_version_id column
    op.add_column('templates',
                  sa.Column('default_version_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create foreign key for default_version_id
    op.create_foreign_key(
        'fk_templates_default_version_id',
        'templates', 'template_versions',
        ['default_version_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create unique constraint for (name, org_id) where org_id is not null
    # Note: This will only work for org-scoped templates. System templates need application-level validation.
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'uq_template_name_org_id'
            ) THEN
                ALTER TABLE templates 
                ADD CONSTRAINT uq_template_name_org_id 
                UNIQUE (name, org_id);
            END IF;
        END $$;
    """)
    
    # Create unique constraint for (template_id, version) in template_versions
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'uq_template_version'
            ) THEN
                ALTER TABLE template_versions 
                ADD CONSTRAINT uq_template_version 
                UNIQUE (template_id, version);
            END IF;
        END $$;
    """)
    
    # Create indexes
    op.create_index('idx_template_system_name', 'templates', ['name'],
                    postgresql_where=sa.text('is_system_template = true'),
                    if_not_exists=True)
    
    op.create_index('idx_template_version_lookup', 'template_versions', ['template_id', 'version'],
                    if_not_exists=True)
    
    op.create_index('ix_templates_is_system_template', 'templates', ['is_system_template'],
                    if_not_exists=True)
    
    # Migrate existing templates: ensure they have org_id set and is_system_template=false
    op.execute("""
        UPDATE templates 
        SET is_system_template = false 
        WHERE is_system_template IS NULL OR org_id IS NOT NULL;
    """)
    
    # Set default_version_id to the first version for existing templates
    op.execute("""
        UPDATE templates t
        SET default_version_id = (
            SELECT tv.id 
            FROM template_versions tv 
            WHERE tv.template_id = t.id 
            ORDER BY tv.version ASC 
            LIMIT 1
        )
        WHERE default_version_id IS NULL;
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_templates_is_system_template', table_name='templates', if_exists=True)
    op.drop_index('idx_template_version_lookup', table_name='template_versions', if_exists=True)
    op.drop_index('idx_template_system_name', table_name='templates', if_exists=True)
    
    # Drop constraints
    op.drop_constraint('uq_template_version', 'template_versions', type_='unique', if_exists=True)
    op.drop_constraint('uq_template_name_org_id', 'templates', type_='unique', if_exists=True)
    
    # Drop foreign key
    op.drop_constraint('fk_templates_default_version_id', 'templates', type_='foreignkey', if_exists=True)
    
    # Drop columns
    op.drop_column('templates', 'default_version_id')
    op.drop_column('templates', 'is_system_template')
    
    # Make org_id not nullable again
    op.execute("""
        UPDATE templates SET org_id = (
            SELECT id FROM organizations LIMIT 1
        ) WHERE org_id IS NULL;
    """)
    op.alter_column('templates', 'org_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False,
                    existing_nullable=True)

