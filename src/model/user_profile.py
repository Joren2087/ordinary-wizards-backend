from flask import current_app
from sqlalchemy import String, BigInteger, Column, Boolean
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.model.credentials import Credentials, PasswordCredentials


class UserProfile(current_app.db.Model):
    """
    A user profile is a representation of a user in the database
    It contains information about the user, such as their name, their credentials, and their player object
    Game specific data such as statisitcs, inventory, etc. are stored in the player object
    """
    __tablename__ = "user_profile"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    player: Mapped["Player"] = relationship("Player", back_populates="user_profile", cascade="all, delete-orphan")
    firstname: Mapped[str] = Column(String(255), nullable=False)
    lastname: Mapped[str] = Column(String(255), nullable=False)
    username: Mapped[str] = Column(String(255), unique=True)
    admin: Mapped[bool] = Column(Boolean(), default=False, server_default="false", nullable=False)

    credentials: Mapped[Credentials] = relationship(back_populates="user_profile", uselist=False, cascade="all, delete-orphan")

    def __init__(self, username: str, firstname: str, lastname: str, credentials: Credentials, admin: bool = False):
        """
        Initializes the user profile object
        :param username: The username of the user, unique
        :param firstname: The first name of the user
        :param lastname: The last name of the user
        :param credentials: The credentials object of the user
        :param admin: Whether the user is an admin or not. Defautls to false
        """
        self.username = username
        self.firstname = firstname
        self.lastname = lastname
        self.credentials = credentials
        from src.model.player import Player
        self.player = Player(user_profile=self, xp=0, mana=0, crystals=0, last_login=None, last_logout=None)
        self.admin = admin

    def uses_oauth2(self):
        """
        Check if the user uses OAuth2 for authentication
        :return: True if the user uses OAuth2, False otherwise (when eg. using password)
        """
        return not isinstance(self.credentials, PasswordCredentials)

    def __repr__(self):
        return f'<UserProfile {self.id} {self.username}>'

    def update(self, data: dict):
        """
        Update the user profile with new data
        Only firstname & lastname can be updated
        :param data: The new data
        :return:
        """
        self.firstname = data.get('firstname', self.firstname)
        self.lastname = data.get('lastname', self.lastname)
        self.admin = data.get('admin', self.admin)


