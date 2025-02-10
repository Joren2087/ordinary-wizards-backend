"""add wall blueprint

Revision ID: 00aa5ef93b81
Revises: 7b87cc5483ea
Create Date: 2024-04-24 17:25:40.974032

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = '00aa5ef93b81'
down_revision = '7b87cc5483ea'
branch_labels = None
depends_on = None


def upgrade():

    # Just a bit of data migration
    # Populate the db with new blueprints
    print("INFO Inserting Wall blueprint")
    # We need to do this with raw SQL as SQLAlchemy already knows there's a new column, but the DB doesn't have that column yet (as it's in a later migration)
    op.execute("INSERT INTO blueprint (id, name, description, cost) VALUES (8, 'Wall', 'A wall to keep enemies from entering your base', 500)")

def downgrade():
    op.execute("DELETE FROM blueprint WHERE id = 8")
