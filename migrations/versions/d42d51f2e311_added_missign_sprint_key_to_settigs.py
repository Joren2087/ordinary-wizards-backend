"""added missign sprint key to settigs

Revision ID: d42d51f2e311
Revises: 1238f3f93719
Create Date: 2024-05-30 19:12:43.363036

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd42d51f2e311'
down_revision = '1238f3f93719'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sprint_key', sa.String(length=12), nullable=False, server_default='ShiftLeft'))
        batch_op.add_column(sa.Column('sprint_val', sa.String(length=12), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_settings', schema=None) as batch_op:
        batch_op.drop_column('sprint_val')
        batch_op.drop_column('sprint_key')

    # ### end Alembic commands ###
