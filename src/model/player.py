import datetime
from typing import List

from flask import current_app
from sqlalchemy import BigInteger, ForeignKey, Column, Integer, CheckConstraint, DateTime, func, PrimaryKeyConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.model.chat_message import ChatMessage
from src.model.spell import Spell
from src.model.user_profile import UserProfile

friends_association_table = current_app.db.Table(
    'friends_association', current_app.db.Model.metadata,
    Column('player_id', BigInteger, ForeignKey('player.user_profile_id', ondelete='CASCADE')),
    Column('friend_id', BigInteger, ForeignKey('player.user_profile_id', ondelete='CASCADE')),
    PrimaryKeyConstraint('player_id', 'friend_id'),
    CheckConstraint('player_id != friend_id')
)


class Player(current_app.db.Model):
    """
    A Player is a profile for a user, containing information about their level, crystals, mana, and spells
    It has a one-to-one, weak relationship with the UserProfile (that holds more sensitive information such as username
    and password hash)

    Everything game related is stored in the Player profile
    It is not an entity, that is the task of the one-to-one associated PlayerEntity object. This is because an
    userprofile id (PK of UserProfile & Player) differs from an entity id (PK of Entity)
    For more details, see the ER diagram in the docs
    """

    user_profile_id: Mapped[BigInteger] = mapped_column(ForeignKey('user_profile.id'), primary_key=True)
    user_profile: Mapped[UserProfile] = relationship("UserProfile", back_populates="player", single_parent=True, foreign_keys=[user_profile_id])

    crystals: Mapped[int] = Column(BigInteger, CheckConstraint('crystals >= 0'), nullable=False, default=0)
    mana: Mapped[int] = Column(Integer, CheckConstraint('mana >= 0 AND mana <= 1000'), nullable=False, default=0)
    xp: Mapped[int] = Column(Integer, CheckConstraint('xp >= 0'), nullable=False, default=0)
    last_logout: Mapped[DateTime] = Column(DateTime, nullable=False, default=0)
    last_login: Mapped[DateTime] = Column(DateTime, nullable=False, default=func.now())

    # entity_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('player_entity.entity_id'))
    # entity: Mapped["PlayerEntity"] = relationship("PlayerEntity", foreign_keys=[entity_id], back_populates="player")
    entity: Mapped['PlayerEntity'] = relationship(back_populates="player", cascade="all, delete-orphan", uselist=False, lazy=False)

    # lazy=False means that the spells are loaded when the player is loaded
    # spells: Mapped[List[Spell]] = relationship(lazy=False, secondary=player_spell_association_table)
    spells_association = relationship("PlayerSpellAssociation", cascade="all, delete-orphan")
    spells: Mapped[List[Spell]] = association_proxy('spells_association', 'spell', creator=lambda map: PlayerSpellAssociation(player_id=map['player_id'], spell_id=map['spell_id'], slot=map['slot'] if 'slot' in map else None))

    # The island of the player
    island: Mapped["Island"] = relationship("Island", back_populates="owner", single_parent=True, cascade="all, delete-orphan")

    # User settings
    user_settings: Mapped["UserSettings"] = relationship("UserSettings", back_populates="player", single_parent=True, cascade="all, delete-orphan")

    # The gem inventory of the player
    gems: Mapped[List["Gem"]] = relationship("Gem", cascade="all, delete-orphan")

    # The player chat messages
    chat_messages: Mapped[List[ChatMessage]] = relationship("ChatMessage", back_populates="user", cascade="save-update")

    # The player friends
    friends: Mapped[List["Player"]] = relationship("Player", secondary=friends_association_table, uselist=True, primaryjoin=user_profile_id == friends_association_table.c.player_id, secondaryjoin=user_profile_id == friends_association_table.c.friend_id)

    # The player's match queue entry
    match_queue_entry: Mapped["MatchQueueEntry"] = relationship("MatchQueueEntry", back_populates="player", uselist=False, cascade="all, delete-orphan")

    # The player's statistics object
    stats: Mapped["PlayerStats"] = relationship("PlayerStats", back_populates="player", uselist=False, cascade="all, delete-orphan")

    def __init__(self, user_profile=None, crystals: int = 0, mana: int = 0, xp: int = None, last_logout: DateTime = None, last_login: DateTime = None):
        """
        Initialize the player class
        :param user_profile: The UserProfile of this player. Should be unique to this player (one-to-one)
        :param crystals: The amount of crystals of the player. Should be >= 0
        :param mana: The amount of mana of the player. Should be >= 0
        :param xp: The amount of experience points of the player. Should be >= 0
        :param last_logout: The last logout time of the player
        :param last_login: The last login time of the player
        """
        if xp < 0:
            raise ValueError("XP must be greater than or equal to 0")
        if crystals < 0:
            raise ValueError("Crystals must be greater than or equal to 0")
        if mana < 0 or mana > 1000: # we allow until a 1000 because you can expand your mana pool
            raise ValueError("Mana must be greater than or equal to 0 and less than or equal to 1000")
        if last_logout is None:
            last_logout = datetime.datetime(1970,1,1)  # epoch
        if last_login is None:
            last_login = func.now()

        self.user_profile = user_profile
        self.crystals = crystals
        self.mana = mana
        self.xp = xp
        self.last_logout = last_logout
        self.last_login = last_login

    def update(self, data: dict):
        """
        Update the player profile with new data
        Friends, blueprints and spells have to be integer arrays whose elements are the id's of the respective objects
        :param data: The new data
        :return:
        """
        if data.get('xp', self.xp) < 0:
            raise ValueError("XP must be greater than or equal to 0")
        if data.get('crystals', self.crystals) < 0:
            raise ValueError("Crystals must be greater than or equal to 0")
        if data.get('mana', self.mana) < 0 or data.get('mana', self.mana) > 1000:
            raise ValueError("Mana must be greater than or equal to 0 and less than or equal to 1000")

        self.crystals = data.get('crystals', self.crystals)
        self.mana = data.get('mana', self.mana)
        self.xp = data.get('xp', self.xp)
        self.last_logout = data.get('last_logout', self.last_logout)
        self.last_login = data.get('last_login', self.last_login)

        if 'spells' in data:
            # ignore pyCharm warning about data types, it's wrong
            from src.resource.player import PlayerSpellAssociationSchema
            for spell in data.get('spells'):
                PlayerSpellAssociationSchema(**spell)

                # Only slot is updatable
                for assoc in self.spells_association:
                    spell["player_id"] = self.user_profile_id  # It MUST be the same, always
                    if assoc.spell_id == spell['spell_id']:
                        assoc.slot = spell.get('slot', assoc.slot)
                        break


        if 'entity' in data:
            self.entity.update(data['entity'])

        if 'friends' in data:
            new_friendset = []
            for friend_id in data.get('friends'):
                if friend_id == self.user_profile_id:
                    raise ValueError("Feeling lonely? (You can't be friends with yourself)")
                friend = Player.query.get(friend_id)
                if friend is None:
                    raise ValueError(f"Friend {friend_id} not found")
                new_friendset.append(friend)
                friend.friends.append(self)  # add the player to the friend's friend list

            # Update the friends their relation to us as well, as the friends relation is a bidirectional many-to-many relationship
            diff = set(self.friends) - set(new_friendset)
            if diff:
                for friend in diff:
                    friend.friends.remove(self)  # remove the player from the friend's friend list

            self.friends = new_friendset


class PlayerSpellAssociation(current_app.db.Model):
    """
    Represents the relationship between a player and a spell with a slot as relationship attribute
    """
    __tablename__ = 'player_spells'

    player_id: Mapped[int] = Column(Integer, ForeignKey('player.user_profile_id', ondelete='CASCADE'), primary_key=True)
    spell_id: Mapped[int] = Column(Integer, ForeignKey('spell.id', ondelete='CASCADE'), primary_key=True)
    slot: Mapped[int] = Column(Integer, CheckConstraint("slot >= 0 AND slot < 5"), nullable=True)  # The slot in which the spell is stored (0-5) - relationship attribute

    player: Mapped[Player] = relationship("Player", back_populates="spells_association")
    spell: Mapped[Spell] = relationship("Spell")

    def __init__(self, player_id: int = None, spell_id: int = None, slot: int = None, **kwargs):
        # leave **kwargs in case of future use
        self.player_id = player_id
        self.spell_id = spell_id
        self.slot = slot
