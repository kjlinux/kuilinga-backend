"""add profile picture to user

Revision ID: 7ce0bb932745
Revises: e640c8f2ecb2
Create Date: 2025-10-21 15:14:30.979236

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ce0bb932745'
down_revision = 'e640c8f2ecb2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('profile_picture_url', sa.String(), nullable=True))


def downgrade():
    op.drop_column('users', 'profile_picture_url')
