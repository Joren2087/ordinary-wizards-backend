import logging

from flask import current_app
from sqlalchemy import BigInteger, Enum, Column, ForeignKey, SmallInteger, String, Float, Boolean
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.model.enums import GemType


class Gem(current_app.db.Model):
    """
    A gem is a special type of item that can be used to boost buildings or mines
    A gem is unique, but can have multiple attributes (from the same set) with different multipliers
    A gem is always associated with a player, but can also be associated with a building (if it is used to boost said building)
    """

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[GemType] = Column(Enum(GemType), default=GemType, nullable=False)

    # The many-to-one relationsip between gems and buildings
    building_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('building.placeable_id'), nullable=True)

    # The many-to-one relationship between gems and players
    player_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('player.user_profile_id'), nullable=False)

    # Wether this gem is used as a stake in a multiplayer game or not
    staked: Mapped[bool] = Column(Boolean(), nullable=False, default=False)

    # attributes: Mapped[list] = relationship('GemAttribute', secondary=association_table)
    attributes_association = relationship("GemAttributeAssociation", cascade="all, delete-orphan")

    # Using association proxy to access multiplier value
    # Ignore the type warning, it's wrong
    # The multiplier CHECK >= 0 is ignored here as this is a very complex thing that now somehow works, but is considered
    # legacy code and should not be touched unless you're God and you know what you're doing
    # Also, the migration aa541bef480 adds a table-level constraint for the multiplier >= 0 already, so if SQLAlchemy doesn't
    # catch it, the database will
    attributes = association_proxy('attributes_association', 'attribute',
                                   creator=lambda map: GemAttributeAssociation(
                                       gem_id=map['gem_id'],
                                       gem_attribute_id=map['gem_attribute_id'],
                                       multiplier=map['multiplier']
                                   ))

    def __init__(self, type: str = None, attributes=None, player_id: int = None, building_id: int = None, staked: bool = False):
        if attributes is None:
            attributes = []

        if not GemType.has_value(type):
            raise ValueError('Invalid gem type')

        self.type = GemType[type.upper()]
        self.attributes = attributes
        self.player_id = player_id
        self.building_id = building_id
        self.staked = staked


    def update(self, data: dict):
        """
        Update the gem object with the given data
        The attributes list of the data input will be synced with the gem's attributes
        Deleting attributes is currently NOT supported, only adding and updating existing ones.
        As a temporary workaround for unable to delete attributes, you can set the multiplier to 0

        Only one of the collding_keys (atm building_id, mine_id and player_id) can be present in the data object.
        This is because a gem can only belong to a single inventory at a time (either a building, a mine or the player inventory)
        :param data: The new data
        :return:
        """


        if 'type' in data:
            if not GemType.has_value(data['type']):
                raise ValueError('Invalid gem type')
            self.type = GemType[data['type'].upper()]

        if 'staked' in data:
            if not isinstance(data['staked'], bool):
                raise ValueError('staked must be a boolean')
            self.staked = data['staked']

        if 'attributes' in data:
            copy = data['attributes'].copy()
            seen_ids = [assoc.attribute.id for assoc in self.attributes_association]
            added_ids = []
            for obj in copy:
                if 'gem_attribute_id' not in obj or 'multiplier' not in obj:
                    raise ValueError('Invalid attribute object. Either gem_attribute_id and/or multiplier is missing')

                if 'gem_attribute_id' in obj:
                    if not GemAttribute.query.get(obj['gem_attribute_id']):
                        raise ValueError('Invalid gem_attribute_id')

                if 'multiplier' in obj:
                    if obj['multiplier'] < 0:
                        raise ValueError('Multiplier must be >= 0')

                # Cannot simply clear the map as this would mess with SQLAlchemys internal state of the entity
                # We need therefore to update the existing map with the new values

                # Update existing entries
                found = False
                for assoc in self.attributes_association:
                   if assoc.attribute.id == obj['gem_attribute_id']:
                       assoc.multiplier = obj['multiplier']
                       found = True

                if not found: # If the for loop didn't run
                    if obj['gem_attribute_id'] in seen_ids:
                        raise ValueError('Duplicate gem_attribute_id in attributes list')
                    # Create new entries
                    added_ids.append(obj['gem_attribute_id'])
                    self.attributes_association.append(GemAttributeAssociation(**obj))
                else:
                    # Remove the entry from the data object if it was found in our own attributes
                    copy.remove(obj)

            # Remove any remaining entries in our own attributes that were not found in the data object
            for assoc in self.attributes_association:
                if assoc.gem_attribute_id in added_ids:
                    # Don't remove the entry if it was added in this update - these are also not fully initialized yet
                    continue

                found = False
                for obj in copy:
                    if assoc.attribute.id == obj['gem_attribute_id']:
                        found = True
                        break

                if not found:
                    self.attributes_association.remove(assoc)


        if 'building_id' in data:
            if data['building_id'] is None:
                self.building_id = None
            else:
                from src.model.placeable.building import Building
                if not Building.query.get(data['building_id']):
                    raise ValueError('Invalid building_id')

                self.building_id = int(data['building_id'])

        if 'player_id' in data:
            # Not nullable
            from src.model.player import Player
            if not Player.query.get(data['player_id']):
                raise ValueError('Invalid player_id')

            self.player_id = int(data['player_id'])

        if self.building_id is None and self.player_id is None:
            logging.error(f"Gem {self.id} is orphaned. This is not supposed to happen. Please investigate")

class GemAttribute(current_app.db.Model):
    """
    A GemAttribute is a type of attribute that can be added to a gem
    Only a fixed set of attributes exist, therefore no enum is defined on the type
    """

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    type: Mapped[str] = Column(String(16), nullable=False, unique=True)

    def __init__(self, id: int = None, type: str = None):
        self.id = id
        self.type = type


# Association Object for Gem-GemAttribute with multiplier
class GemAttributeAssociation(current_app.db.Model):
    """
    Represents the relationship between a gem and a gem attribute with a multiplier as relationship attribute
    """
    __tablename__ = 'gem_attribute_association'
    gem_id = Column(BigInteger, ForeignKey('gem.id'), primary_key=True)
    gem_attribute_id = Column(SmallInteger, ForeignKey('gem_attribute.id'), primary_key=True)
    multiplier = Column(Float)
    gem = relationship("Gem", back_populates="attributes_association")
    attribute = relationship("GemAttribute")

    def __init__(self, gem_id: int = None, gem_attribute_id: int = None, multiplier: float = None, **kwargs):
        # leave **kwargs in case of future use
        self.gem_id = gem_id
        self.gem_attribute_id = gem_attribute_id
        self.multiplier = multiplier






