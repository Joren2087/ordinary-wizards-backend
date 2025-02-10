"""add CHECK constraints

Revision ID: aa541bef480
Revises: a30fac7d53b1
Create Date: 2024-04-06 20:39:07.493918

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = 'aa541bef480'
down_revision = 'a30fac7d53b1'
branch_labels = None
depends_on = None


def upgrade():
    # Add check constraints to the building table
    op.create_check_constraint('ck_building_level', 'building', 'level >= 0')

    # Add check constraints to the placeable table
    op.create_check_constraint('ck_placeable_xpos', 'placeable', 'xpos >= -7 AND xpos <= 7')
    op.create_check_constraint('ck_placeable_zpos', 'placeable', 'zpos >= -7 AND zpos <= 7')
    op.create_check_constraint('ck_placeable_rotation', 'placeable', 'rotation >= 0 AND rotation <= 3')

    # Add check constraints to the blueprint table
    op.create_check_constraint('ck_blueprint_cost', 'blueprint', 'cost >= 0')
    op.create_check_constraint('ck_blueprint_buildtime', 'blueprint', 'buildtime >= 0')

    # Add check constraints to the building_upgrade_task table
    op.create_check_constraint('ck_building_upgrade_task_used_crystals', 'building_upgrade_task', 'used_crystals >= 0')
    op.create_check_constraint('ck_building_upgrade_task_used_to_level', 'building_upgrade_task', 'to_level >= 0')

    # Add check constraints to the entity table
    op.create_check_constraint('ck_entity_level', 'entity', 'level >= 0')

    # Add check constraints to the gem_attribute_association table
    op.create_check_constraint('ck_gem_attribute_association_multiplier', 'gem_attribute_association', 'multiplier >= 0')

    # Add check constraints to the mine_building table
    op.create_check_constraint('ck_mine_building_mined_amount', 'mine_building', 'mined_amount >= 0')

    # Add check constraints to the player table
    op.create_check_constraint('ck_player_crystals', 'player', 'crystals >= 0')
    op.create_check_constraint('ck_player_mana', 'player', 'mana >= 0 AND mana <= 1000')
    op.create_check_constraint('ck_player_xp', 'player', 'xp >= 0')

    # Add check constraints to the user_settings table
    op.create_check_constraint('ck_user_settings_audio_volume', 'user_settings', 'audio_volume >= 0 AND audio_volume <= 100')


def downgrade():
    # Remove check constraints from the building table
    op.drop_constraint('ck_building_level', 'building')

    # Remove check constraints from the placeable table
    op.drop_constraint('ck_placeable_xpos', 'placeable')
    op.drop_constraint('ck_placeable_zpos', 'placeable')
    op.drop_constraint('ck_placeable_rotation', 'placeable')

    # Remove check constraints from the blueprint table
    op.drop_constraint('ck_blueprint_cost', 'blueprint')
    op.drop_constraint('ck_blueprint_buildtime', 'blueprint')

    # Remove check constraints from the building_upgrade_task table
    op.drop_constraint('ck_building_upgrade_task_used_crystals', 'building_upgrade_task')
    op.drop_constraint('ck_building_upgrade_task_used_to_level', 'building_upgrade_task')

    # Remove check constraints from the entity table
    op.drop_constraint('ck_entity_level', 'entity')

    # Remove check constraints from the gem_attribute_association table
    op.drop_constraint('ck_gem_attribute_association_multiplier', 'gem_attribute_association')

    # Remove check constraints from the mine_building table
    op.drop_constraint('ck_mine_building_mined_amount', 'mine_building')

    # Remove check constraints from the player table
    op.drop_constraint('ck_player_crystals', 'player')
    op.drop_constraint('ck_player_mana', 'player')
    op.drop_constraint('ck_player_xp', 'player')

    # Remove check constraints from the user_settings table
    op.drop_constraint('ck_user_settings_audio_volume', 'user_settings')
