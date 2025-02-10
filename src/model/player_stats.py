from flask import current_app
from sqlalchemy import Integer, Column, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, Mapped


class PlayerStats(current_app.db.Model):
    """
    A PlayerStats object is a collection of multiplayer statistics for a player
    """

    player_id: Mapped[int] = Column(Integer, ForeignKey('player.user_profile_id'), primary_key=True)
    player: Mapped['Player'] = relationship("Player", back_populates="stats")

    player_kills: Mapped[int] = Column(Integer, CheckConstraint("player_kills >= 0"), default=0)
    player_deaths: Mapped[int] = Column(Integer, CheckConstraint("player_deaths >= 0"), default=0)
    minions_killed: Mapped[int] = Column(Integer, CheckConstraint("minions_killed >= 0"), default=0)
    damage_dealt: Mapped[int] = Column(Integer, CheckConstraint("damage_dealt >= 0"), default=0)
    damage_taken: Mapped[int] = Column(Integer, CheckConstraint("damage_taken >= 0"), default=0)
    mana_spent: Mapped[int] = Column(Integer, CheckConstraint("mana_spent >= 0"), default=0)
    spell_casts: Mapped[int] = Column(Integer, CheckConstraint("spell_casts >= 0"), default=0)
    gems_won: Mapped[int] = Column(Integer, CheckConstraint("gems_won >= 0"), default=0)
    gems_lost: Mapped[int] = Column(Integer, CheckConstraint("gems_lost >= 0"), default=0)
    games_played: Mapped[int] = Column(Integer, CheckConstraint("games_played >= 0"), default=0)
    games_won: Mapped[int] = Column(Integer, CheckConstraint("games_won >= 0"), default=0)


    def __init__(self, player_id: int = None, player_kills: int = None, player_deaths: int = None, minions_killed: int = None, damage_dealt: int = None, damage_taken: int = None, mana_spent: int = None, spell_casts: int = None, gems_won: int = None, gems_lost: int = None, games_played: int = None, games_won: int = None, **kwargs):
        # leave **kwargs in case of future use
        self.player_id = player_id
        self.player_kills = player_kills
        self.player_deaths = player_deaths
        self.minions_killed = minions_killed
        self.damage_dealt = damage_dealt
        self.damage_taken = damage_taken
        self.mana_spent = mana_spent
        self.spell_casts = spell_casts
        self.gems_won = gems_won
        self.gems_lost = gems_lost
        self.games_played = games_played
        self.games_won = games_won


    def update(self, data):
        """
        Update the player statistics with new data
        All fields are updatable
        :param data:
        :return:
        """
        self.player_kills = data.get('player_kills', self.player_kills)
        self.player_deaths = data.get('player_deaths', self.player_deaths)
        self.minions_killed = data.get('minions_killed', self.minions_killed)
        self.damage_dealt = data.get('damage_dealt', self.damage_dealt)
        self.damage_taken = data.get('damage_taken', self.damage_taken)
        self.mana_spent = data.get('mana_spent', self.mana_spent)
        self.spell_casts = data.get('spell_casts', self.spell_casts)
        self.gems_won = data.get('gems_won', self.gems_won)
        self.gems_lost = data.get('gems_lost', self.gems_lost)
        self.games_played = data.get('games_played', self.games_played)
        self.games_won = data.get('games_won', self.games_won)

