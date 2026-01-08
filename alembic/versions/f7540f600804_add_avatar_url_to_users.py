"""add_avatar_url_to_users

Revision ID: f7540f600804
Revises: ef4fc77c35c3
Create Date: 2026-01-08 14:49:16.792454

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f7540f600804'
down_revision = 'ef4fc77c35c3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))


def downgrade():
    op.drop_column('users', 'avatar_url')
