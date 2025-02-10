from flask import current_app
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship, declared_attr

from src.model.player import Player


class Island(current_app.db.Model):
    """
    An island is a collection of entities and placeables (buildings) that are placed on a grid.
    It contains all necessary values to load in an island of a player.
    An island is unique to it's owner, and is not shared between players.
    """

    owner_id: Mapped[int] = mapped_column(ForeignKey('player.user_profile_id', use_alter=True, ondelete="cascade"), primary_key=True)

    @declared_attr
    def owner(self):
        return relationship("Player", back_populates="island", single_parent=True, foreign_keys=[self.owner_id])

    @declared_attr
    def entities(self):
        return relationship("Entity", back_populates="island", cascade="all, delete-orphan")

    @declared_attr
    def placeables(self):
        return relationship("Placeable", back_populates="island", cascade="all, delete-orphan")

    @declared_attr
    def tasks(self):
        return relationship("Task", back_populates="island", cascade="all, delete-orphan")

    def __init__(self, owner: Player = None):
       self.owner = owner
       self.owner_id = owner.user_profile_id