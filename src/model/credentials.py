from abc import abstractmethod

import bcrypt
from flask import current_app
from sqlalchemy import ForeignKey, BigInteger, Column, String, LargeBinary
from sqlalchemy.orm import relationship, mapped_column, Mapped


class Credentials(current_app.db.Model):
    """
    Abstract base class for credentials
    Credentials are used to authenticate a user, it can be a password, an OAuth token, etc.
    Each credential has a one to one relationship with a user profile
    Each credential object has its own ID (primary key), due to SQLAlchemy limitations
    """
    __tablename__ = "credentials"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[str] = Column(String(32)) # Keep track of polymorphic identities
    user_profile_id: Mapped[int] = mapped_column(ForeignKey('user_profile.id'))
    user_profile = relationship("UserProfile", back_populates="credentials", uselist=False)

    @abstractmethod
    def authenticate(self, loginData: dict) -> bool:
        pass

    __mapper_args__ = {
        'polymorphic_abstract': True,
        'polymorphic_on': type
    }


class PasswordCredentials(Credentials):
    """
    A credentials object that stores a password hash and salt
    Passwords are hashed using bcrypt + a random salt, which is a secure and slow hashing algorithm
    """
    id: Mapped[int] = mapped_column(BigInteger, ForeignKey("credentials.id"), primary_key=True)

    password_hash = Column(LargeBinary(128), nullable=False)
    password_salt = Column(LargeBinary(128), nullable=False)

    def __init__(self, password_hash, password_salt):
        self.password_hash = password_hash
        self.password_salt = password_salt


    def authenticate(self, loginData: dict) -> bool:
        """
        Attempts authentication by checking if the user provided password matches the stored hash
        This comparisations is safe from timing attacks as per bcrypt's design
        :param loginData: The logindata, containing the plaintext password in a dict
        :return: True if the password matches, False otherwise
        """
        assert 'password' in loginData, "Password not provided"
        # Timing attack safe function
        match = bcrypt.checkpw(loginData['password'].encode('utf-8'), self.password_hash)
        return match

    def change_password(self, new_password: str):
        """
        Change the password by creating a new hash with a new salt
        :param new_password: The new plaintext password
        """
        self.password_salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), self.password_salt)


    @staticmethod
    def create_from_password(password: str) -> 'PasswordCredentials':
        """
        Create a new PasswordCredentials object from a password string
        A random, cryptographically secure salt is generated and stored with the hash
        :param password: The plaintext password
        :return: The PasswordCredentials object
        """
        password_salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), password_salt)
        return PasswordCredentials(password_hash, password_salt)

    __mapper_args__ = {
        'polymorphic_identity': 'password_credentials'
    }


class OAuth2Credentials(Credentials):
    """
    An OAuth2Credentials object that stores the OAuth2 user ID (eg Google ID)
    """
    id: Mapped[int] = mapped_column(BigInteger, ForeignKey("credentials.id"), primary_key=True)

    # The OAuth2 ID of the user
    # Stored as a string since the ID can be longer than a number or contain characters
    sso_id = Column(String(21), nullable=False, unique=True)

    def __init__(self, sso_id: str):
        self.sso_id = sso_id


    def authenticate(self, loginData: dict) -> bool:
        """
        Attempts authentication by checking if the user provided SSO ID matches the stored SSO ID
        The SSO ID is unique and cannot be changed, so it's safe to use it for authentication
        :param loginData: The logindata, containing the SSO ID in a dict
        :return: True if the SSO IDs match, False otherwise
        """
        assert 'sso_id' in loginData, "sso_id not provided"
        return loginData['sso_id'] == self.sso_id


    __mapper_args__ = {
        'polymorphic_identity': 'oauth2_credentials'
    }