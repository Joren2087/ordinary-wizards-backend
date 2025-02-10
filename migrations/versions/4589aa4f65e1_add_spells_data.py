"""Add spells data

Revision ID: 4589aa4f65e1
Revises: e18abe977e53
Create Date: 2024-04-13 14:53:44.969927

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4589aa4f65e1'
down_revision = '081d41bb3cad'
branch_labels = None
depends_on = None


def upgrade():
    """
    In order to cascade the changes, we need to update the foreign key constraint
    But we cannot update a constraint, so we have to remvoe it and then recreate it with the proper cascade policies
    Then, we finally truncate the table spell
    :return:
    """
    op.execute("DELETE FROM spell CASCADE WHERE true;")  # Nuke it lol

    spells = [
        {"id": 0, "name": "BuildSpell"},
        {"id": 1, "name": "Fireball"},
        {"id": 2, "name": "IceWall"},
        {"id": 3, "name": "Zap"},
        {"id": 4, "name": "ThunderCloud"},
        {"id": 5, "name": "Shield"},
        {"id": 6, "name": "Heal"}
    ]
    op.bulk_insert(
        sa.Table('spell', sa.MetaData(),
                 sa.Column('id', sa.Integer(), primary_key=True),
                 sa.Column('name', sa.String(255), nullable=False)
                 ),
        spells
    )


def downgrade():
    op.execute("DELETE FROM spell CASCADE WHERE true;")  # Nuke it lol

