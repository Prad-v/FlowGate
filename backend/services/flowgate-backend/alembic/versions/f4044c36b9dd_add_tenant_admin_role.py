"""add tenant admin role

Revision ID: f4044c36b9dd
Revises: 015_add_iam_rbac_tables
Create Date: 2025-11-24 05:19:06.123456

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import uuid

# revision identifiers, used by Alembic.
revision = 'f4044c36b9dd'
down_revision = '015_add_iam_rbac_tables'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    
    # Get existing role IDs
    result = conn.execute(text("SELECT id, name FROM roles WHERE name IN ('super_admin', 'org_admin')"))
    roles = {row[1]: row[0] for row in result}
    
    super_admin_role_id = roles.get('super_admin')
    org_admin_role_id = roles.get('org_admin')
    
    if not super_admin_role_id or not org_admin_role_id:
        raise Exception("Required roles (super_admin, org_admin) not found")
    
    # Create tenant_admin role
    tenant_admin_role_id = uuid.uuid4()
    conn.execute(text("""
        INSERT INTO roles (id, name, description, is_system_role, created_at, updated_at)
        VALUES (:id, 'tenant_admin', 'Tenant Administrator with full access to tenant resources', true, NOW(), NOW())
    """), {'id': tenant_admin_role_id})
    
    # Assign permissions to tenant_admin
    # Tenant admin gets all permissions except organization management and wildcard manage
    # Similar to org_admin but with tenant-specific scope
    wildcard_manage = '*:manage'
    conn.execute(text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT :role_id, id FROM permissions
        WHERE name NOT LIKE 'organizations:%%' AND name <> :wildcard_manage
    """), {'role_id': tenant_admin_role_id, 'wildcard_manage': wildcard_manage})
    
    # Also add organization read for tenant admin
    conn.execute(text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT :role_id, id FROM permissions WHERE name = 'organizations:read'
    """), {'role_id': tenant_admin_role_id})


def downgrade():
    conn = op.get_bind()
    
    # Remove tenant_admin role and its permissions
    result = conn.execute(text("SELECT id FROM roles WHERE name = 'tenant_admin'"))
    role_row = result.fetchone()
    
    if role_row:
        tenant_admin_role_id = role_row[0]
        # Delete role permissions
        conn.execute(text("DELETE FROM role_permissions WHERE role_id = :role_id"), {'role_id': tenant_admin_role_id})
        # Delete user roles
        conn.execute(text("DELETE FROM user_roles WHERE role_id = :role_id"), {'role_id': tenant_admin_role_id})
        # Delete role
        conn.execute(text("DELETE FROM roles WHERE id = :role_id"), {'role_id': tenant_admin_role_id})
