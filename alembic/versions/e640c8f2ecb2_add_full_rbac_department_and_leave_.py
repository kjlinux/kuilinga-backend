"""Add full RBAC, Department, and Leave models

Revision ID: e640c8f2ecb2
Revises:
Create Date: 2023-10-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e640c8f2ecb2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### Layer 1: Base tables with no dependencies ###
    
    # 1. Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=True, server_default='UTC'),
        sa.Column('plan', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_organizations_name', 'name'),
        sa.Index('ix_organizations_email', 'email', unique=True)
    )
    
    # 2. Create permissions table
    op.create_table('permissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index(op.f('ix_permissions_name'), 'name', unique=True)
    )
    
    # 3. Create roles table
    op.create_table('roles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index(op.f('ix_roles_name'), 'name', unique=True)
    )
    
    # ### Layer 2: Tables depending on Layer 1 ###
    
    # 4. Create sites table (depends on organizations)
    op.create_table('sites',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=True, server_default='UTC'),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 5. Create users table (depends on organizations)
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('organization_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_users_email', 'email', unique=True),
        sa.Index('ix_users_phone', 'phone', unique=True),
        sa.Index('ix_users_full_name', 'full_name')
    )
    
    # 6. Create role_permissions junction table
    op.create_table('role_permissions',
        sa.Column('role_id', sa.String(), nullable=False),
        sa.Column('permission_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # 7. Create user_roles junction table
    op.create_table('user_roles',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    
    # 8. Create devices table (depends on organizations, sites)
    op.create_table('devices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('serial_number', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('ONLINE', 'OFFLINE', 'MAINTENANCE', name='devicestatus'), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('site_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_devices_serial_number', 'serial_number', unique=True)
    )
    
    # ### Layer 3: Tables with circular dependencies ###
    
    # 9. Create departments table WITHOUT manager_id FK
    op.create_table('departments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('site_id', sa.String(), nullable=False),
        sa.Column('manager_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index(op.f('ix_departments_name'), 'name', unique=False)
    )
    
    # 10. Create employees table (depends on users, organizations, sites, departments)
    op.create_table('employees',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('employee_number', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('badge_id', sa.String(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('site_id', sa.String(), nullable=True),
        sa.Column('department_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_employees_employee_number', 'employee_number', unique=True),
        sa.Index('ix_employees_email', 'email', unique=True),
        sa.Index('ix_employees_badge_id', 'badge_id', unique=True)
    )
    
    # 11. NOW add the circular FK from departments to employees
    op.create_foreign_key(
        'fk_departments_manager_id',
        'departments', 'employees',
        ['manager_id'], ['id']
    )
    
    # ### Layer 4: Tables depending on employees ###
    
    # 12. Create attendances table
    op.create_table('attendances',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('type', sa.Enum('IN', 'OUT', name='attendancetype'), nullable=False),
        sa.Column('geo', sa.String(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('employee_id', sa.String(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 13. Create leaves table
    op.create_table('leaves',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('employee_id', sa.String(), nullable=False),
        sa.Column('approver_id', sa.String(), nullable=True),
        sa.Column('leave_type', sa.Enum('ANNUAL', 'SICK', 'MATERNITY', 'PATERNITY', 'UNPAID', 'OTHER', name='leavetype'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', name='leavestatus'), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto-generated by Alembic - please adjust! ###
    
    # Drop in reverse order
    op.drop_table('leaves')
    op.drop_table('attendances')
    
    # Drop circular FK first
    op.drop_constraint('fk_departments_manager_id', 'departments', type_='foreignkey')
    
    op.drop_table('employees')
    op.drop_table('departments')
    op.drop_table('devices')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('users')
    op.drop_table('sites')
    
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_table('roles')
    
    op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
    op.drop_table('permissions')
    
    op.drop_table('organizations')
    
    # ### end Alembic commands ###