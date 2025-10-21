"""add password reset token to user

Revision ID: 8606a03719fa
Revises: 7ce0bb932745
Create Date: 2025-10-21 15:22:54.674918

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8606a03719fa'
down_revision = '7ce0bb932745'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('password_reset_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('password_reset_token_expires_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('users', 'password_reset_token_expires_at')
    op.drop_column('users', 'password_reset_token')
