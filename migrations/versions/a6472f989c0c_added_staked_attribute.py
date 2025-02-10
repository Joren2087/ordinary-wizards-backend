"""added staked attribute

Revision ID: a6472f989c0c
Revises: a547169fac51
Create Date: 2024-04-28 18:57:57.656757

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6472f989c0c'
down_revision = 'a547169fac51'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('gem', schema=None) as batch_op:
        batch_op.add_column(sa.Column('staked', sa.Boolean(), nullable=False, default=False, server_default='false'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('gem', schema=None) as batch_op:
        batch_op.drop_column('staked')

    # ### end Alembic commands ###
