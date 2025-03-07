"""add spells

Revision ID: 22389b2496cb
Revises: dc57db68b859
Create Date: 2024-03-11 20:39:07.493918

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22389b2496cb'
down_revision = 'dc57db68b859'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('spell',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('player_spells',
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('spell_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['player_id'], ['player.user_profile_id'], ),
    sa.ForeignKeyConstraint(['spell_id'], ['spell.id'], ),
    sa.PrimaryKeyConstraint('player_id', 'spell_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('player_spells')
    op.drop_table('spell')
    # ### end Alembic commands ###
