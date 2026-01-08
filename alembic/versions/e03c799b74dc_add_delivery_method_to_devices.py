"""add delivery_method to devices

Revision ID: e03c799b74dc
Revises: 120ae6e6ff1b
Create Date: 2026-01-08 01:05:23.933889

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e03c799b74dc'
down_revision = '120ae6e6ff1b'
branch_labels = None
depends_on = None


def upgrade():
    # Créer le type enum pour delivery_method
    delivery_method_enum = sa.Enum('http', 'mqtt', name='deliverymethod')
    delivery_method_enum.create(op.get_bind(), checkfirst=True)

    # Ajouter la colonne delivery_method avec valeur par défaut 'mqtt'
    op.add_column(
        'devices',
        sa.Column(
            'delivery_method',
            sa.Enum('http', 'mqtt', name='deliverymethod'),
            nullable=False,
            server_default='mqtt',
            comment='Méthode de communication: http ou mqtt'
        )
    )


def downgrade():
    # Supprimer la colonne
    op.drop_column('devices', 'delivery_method')

    # Supprimer le type enum
    delivery_method_enum = sa.Enum('http', 'mqtt', name='deliverymethod')
    delivery_method_enum.drop(op.get_bind(), checkfirst=True)
