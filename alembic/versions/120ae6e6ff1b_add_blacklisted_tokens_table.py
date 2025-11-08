"""add blacklisted tokens table

Revision ID: 120ae6e6ff1b
Revises: e640c8f2ecb2
Create Date: 2025-11-08 16:55:48.551263

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '120ae6e6ff1b'
down_revision = 'e640c8f2ecb2'
branch_labels = None
depends_on = None


def upgrade():
    # Create blacklisted_tokens table
    op.create_table(
        'blacklisted_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('blacklisted_on', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blacklisted_tokens_token'), 'blacklisted_tokens', ['token'], unique=True)


def downgrade():
    # Drop blacklisted_tokens table
    op.drop_index(op.f('ix_blacklisted_tokens_token'), table_name='blacklisted_tokens')
    op.drop_table('blacklisted_tokens')
