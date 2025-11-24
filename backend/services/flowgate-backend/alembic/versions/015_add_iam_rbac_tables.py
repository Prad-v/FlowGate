"""Add IAM and RBAC tables

Revision ID: 015_add_iam_rbac_tables
Revises: 014_add_ai_log_platform_tables
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
import uuid
from datetime import datetime
import sys
import os

# Add app to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# revision identifiers, used by Alembic.
revision = '015_add_iam_rbac_tables'
down_revision = '014_add_ai_log_platform_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create OIDC provider type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE oidc_provider_type AS ENUM ('direct', 'proxy');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.String(500)),
        sa.Column('is_system_role', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_roles_name', 'roles', ['name'])

    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_permissions_name', 'permissions', ['name'])

    # Create role_permissions association table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    )

    # Create user_roles table
    op.create_table(
        'user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', 'role_id', 'org_id', name='uq_user_role_org'),
    )
    op.create_index('ix_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('ix_user_roles_role_id', 'user_roles', ['role_id'])
    op.create_index('ix_user_roles_org_id', 'user_roles', ['org_id'])

    # Create oidc_providers table
    # Note: We use String for provider_type initially to avoid SQLAlchemy auto-creating the enum
    # The enum is already created above
    op.create_table(
        'oidc_providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('provider_type', sa.String(20), nullable=False),  # Will be converted to enum after table creation
        sa.Column('issuer_url', sa.String(500)),
        sa.Column('client_id', sa.String(255)),
        sa.Column('client_secret_encrypted', sa.Text()),
        sa.Column('authorization_endpoint', sa.String(500)),
        sa.Column('token_endpoint', sa.String(500)),
        sa.Column('userinfo_endpoint', sa.String(500)),
        sa.Column('proxy_url', sa.String(500)),
        sa.Column('scopes', sa.String(500)),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_oidc_providers_name', 'oidc_providers', ['name'])
    op.create_index('ix_oidc_providers_org_id', 'oidc_providers', ['org_id'])
    
    # Convert provider_type column to use the enum type
    op.execute("""
        ALTER TABLE oidc_providers 
        ALTER COLUMN provider_type TYPE oidc_provider_type 
        USING provider_type::oidc_provider_type
    """)

    # Update users table - add OIDC fields and make org_id nullable
    op.alter_column('users', 'org_id', nullable=True)
    op.alter_column('users', 'hashed_password', nullable=True)
    op.add_column('users', sa.Column('oidc_provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oidc_providers.id'), nullable=True))
    op.add_column('users', sa.Column('oidc_subject', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_users_oidc_provider_id', 'users', ['oidc_provider_id'])
    op.create_index('ix_users_oidc_subject', 'users', ['oidc_subject'])

    # Seed default roles
    conn = op.get_bind()
    
    # Insert system roles
    super_admin_role_id = uuid.uuid4()
    org_admin_role_id = uuid.uuid4()
    org_member_role_id = uuid.uuid4()
    viewer_role_id = uuid.uuid4()
    
    conn.execute(text("""
        INSERT INTO roles (id, name, description, is_system_role, created_at, updated_at)
        VALUES 
        (:super_admin_id, 'super_admin', 'Super Administrator with access to all organizations', true, NOW(), NOW()),
        (:org_admin_id, 'org_admin', 'Organization Administrator with full access within organization', true, NOW(), NOW()),
        (:org_member_id, 'org_member', 'Organization Member with standard read/write access', true, NOW(), NOW()),
        (:viewer_id, 'viewer', 'Viewer with read-only access within organization', true, NOW(), NOW())
    """), {
        'super_admin_id': super_admin_role_id,
        'org_admin_id': org_admin_role_id,
        'org_member_id': org_member_role_id,
        'viewer_id': viewer_role_id
    })

    # Insert default permissions
    permissions_data = [
        # Templates
        (uuid.uuid4(), 'templates:read', 'templates', 'read'),
        (uuid.uuid4(), 'templates:write', 'templates', 'write'),
        (uuid.uuid4(), 'templates:delete', 'templates', 'delete'),
        (uuid.uuid4(), 'templates:manage', 'templates', 'manage'),
        # Gateways
        (uuid.uuid4(), 'gateways:read', 'gateways', 'read'),
        (uuid.uuid4(), 'gateways:write', 'gateways', 'write'),
        (uuid.uuid4(), 'gateways:delete', 'gateways', 'delete'),
        (uuid.uuid4(), 'gateways:manage', 'gateways', 'manage'),
        # Deployments
        (uuid.uuid4(), 'deployments:read', 'deployments', 'read'),
        (uuid.uuid4(), 'deployments:write', 'deployments', 'write'),
        (uuid.uuid4(), 'deployments:delete', 'deployments', 'delete'),
        (uuid.uuid4(), 'deployments:manage', 'deployments', 'manage'),
        # Organizations
        (uuid.uuid4(), 'organizations:read', 'organizations', 'read'),
        (uuid.uuid4(), 'organizations:write', 'organizations', 'write'),
        (uuid.uuid4(), 'organizations:manage', 'organizations', 'manage'),
        # Users
        (uuid.uuid4(), 'users:read', 'users', 'read'),
        (uuid.uuid4(), 'users:write', 'users', 'write'),
        (uuid.uuid4(), 'users:manage', 'users', 'manage'),
        # Settings
        (uuid.uuid4(), 'settings:read', 'settings', 'read'),
        (uuid.uuid4(), 'settings:write', 'settings', 'write'),
        # Security modules
        (uuid.uuid4(), 'security:read', 'security', 'read'),
        (uuid.uuid4(), 'security:write', 'security', 'write'),
        # Wildcard permissions
        (uuid.uuid4(), '*:read', '*', 'read'),
        (uuid.uuid4(), '*:write', '*', 'write'),
        (uuid.uuid4(), '*:manage', '*', 'manage'),
    ]
    
    for perm_id, name, resource_type, action in permissions_data:
        conn.execute(text("""
            INSERT INTO permissions (id, name, resource_type, action, created_at, updated_at)
            VALUES (:id, :name, :resource_type, :action, NOW(), NOW())
        """), {
            'id': perm_id,
            'name': name,
            'resource_type': resource_type,
            'action': action
        })

    # Assign permissions to roles
    # Super Admin: All permissions
    conn.execute(text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT :role_id, id FROM permissions
    """), {'role_id': super_admin_role_id})
    
    # Org Admin: All permissions except organization management and wildcard manage
    # Escape the *:manage string to avoid SQLAlchemy interpreting it as bind param
    wildcard_manage = '*:manage'
    conn.execute(text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT :role_id, id FROM permissions
        WHERE name NOT LIKE 'organizations:%%' AND name <> :wildcard_manage
    """), {'role_id': org_admin_role_id, 'wildcard_manage': wildcard_manage})
    # Also add organization read for org admin
    conn.execute(text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT :role_id, id FROM permissions WHERE name = 'organizations:read'
    """), {'role_id': org_admin_role_id})
    
    # Org Member: Read and write (no delete/manage)
    conn.execute(text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT :role_id, id FROM permissions
        WHERE action IN ('read', 'write') AND resource_type != '*'
    """), {'role_id': org_member_role_id})
    
    # Viewer: Read only
    conn.execute(text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT :role_id, id FROM permissions
        WHERE action = 'read' AND resource_type != '*'
    """), {'role_id': viewer_role_id})

    # Create default super admin user (admin/admin)
    # First, check if a default organization exists, if not create one
    result = conn.execute(text("SELECT id FROM organizations LIMIT 1"))
    org_row = result.fetchone()
    default_org_id = org_row[0] if org_row else None
    
    # Hash password for admin/admin
    # Use bcrypt directly to avoid passlib compatibility issues
    try:
        import bcrypt
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(b"admin", salt).decode('utf-8')
    except Exception as e:
        # Fallback: use a pre-computed bcrypt hash for "admin"
        # This is bcrypt.hashpw(b"admin", b"$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYqYqYqYq")
        # But let's compute it properly
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(b"admin", salt).decode('utf-8')
    
    admin_user_id = uuid.uuid4()
    
    conn.execute(text("""
        INSERT INTO users (id, email, username, hashed_password, full_name, is_active, is_superuser, org_id, password_changed_at, created_at, updated_at)
        VALUES (:id, 'admin@flowgate.local', 'admin', :hashed_password, 'Super Administrator', true, true, :org_id, NULL, NOW(), NOW())
    """), {
        'id': admin_user_id,
        'hashed_password': hashed_password,
        'org_id': default_org_id
    })
    
    # Assign super_admin role to admin user (with org_id = NULL for cross-org access)
    conn.execute(text("""
        INSERT INTO user_roles (id, user_id, role_id, org_id, created_at, updated_at)
        VALUES (:id, :user_id, :role_id, NULL, NOW(), NOW())
    """), {
        'id': uuid.uuid4(),
        'user_id': admin_user_id,
        'role_id': super_admin_role_id
    })


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('oidc_providers')
    op.drop_table('permissions')
    op.drop_table('roles')
    
    # Revert users table changes
    op.drop_index('ix_users_oidc_subject', 'users')
    op.drop_index('ix_users_oidc_provider_id', 'users')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'oidc_subject')
    op.drop_column('users', 'oidc_provider_id')
    op.alter_column('users', 'hashed_password', nullable=False)
    op.alter_column('users', 'org_id', nullable=False)
    
    # Drop enum
    op.execute("DROP TYPE IF EXISTS oidc_provider_type")

