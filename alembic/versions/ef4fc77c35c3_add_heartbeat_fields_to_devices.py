"""add_heartbeat_fields_to_devices

Revision ID: ef4fc77c35c3
Revises: e03c799b74dc
Create Date: 2026-01-08 12:49:29.137099

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ef4fc77c35c3'
down_revision = 'e03c799b74dc'
branch_labels = None
depends_on = None


def upgrade():
    # Add heartbeat tracking columns to devices table
    op.add_column('devices', sa.Column(
        'last_seen_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Dernière communication reçue du terminal (heartbeat ou pointage)'
    ))
    op.add_column('devices', sa.Column(
        'firmware_version',
        sa.String(50),
        nullable=True,
        comment='Version du firmware du terminal'
    ))
    op.add_column('devices', sa.Column(
        'battery_level',
        sa.Integer(),
        nullable=True,
        comment='Niveau de batterie en pourcentage (0-100)'
    ))
    op.add_column('devices', sa.Column(
        'wifi_rssi',
        sa.Integer(),
        nullable=True,
        comment='Force du signal WiFi en dBm (ex: -45)'
    ))


def downgrade():
    # Remove heartbeat tracking columns
    op.drop_column('devices', 'wifi_rssi')
    op.drop_column('devices', 'battery_level')
    op.drop_column('devices', 'firmware_version')
    op.drop_column('devices', 'last_seen_at')
