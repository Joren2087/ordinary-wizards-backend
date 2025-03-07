"""removed collected_amount and gem assoc from mine

Revision ID: 7b87cc5483ea
Revises: 4589aa4f65e1
Create Date: 2024-04-14 18:24:15.052808

"""
import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b87cc5483ea'
down_revision = '4589aa4f65e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('gem', schema=None) as batch_op:
        batch_op.drop_constraint('gem_mine_id_fkey', type_='foreignkey')
        batch_op.drop_column('mine_id')

    with op.batch_alter_table('mine_building', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_collected', sa.DateTime(), nullable=False, server_default=str(datetime.datetime(1970, 1, 1, 0, 0))))
        batch_op.drop_column('mined_amount')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('mine_building', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mined_amount', sa.BIGINT(), autoincrement=False, nullable=False, server_default='0'))
        batch_op.drop_column('last_collected')

    with op.batch_alter_table('gem', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mine_id', sa.BIGINT(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('gem_mine_id_fkey', 'mine_building', ['mine_id'], ['placeable_id'])

    # ### end Alembic commands ###
