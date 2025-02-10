import logging
from typing import Optional

from flask import current_app
from flask_jwt_extended import create_access_token
from flask_sqlalchemy import SQLAlchemy

from src.model.player_stats import PlayerStats
from src.model.player import PlayerSpellAssociation
from src.model.player_entity import PlayerEntity
from src.model.enums import BlueprintType
from src.model.placeable.altar_building import AltarBuilding
from src.model.placeable.mine_building import MineBuilding
from src.model.user_profile import UserProfile
from src.model.island import Island
from src.model.credentials import Credentials, PasswordCredentials, OAuth2Credentials
from src.model.user_settings import UserSettings

db: SQLAlchemy = current_app.db

class AuthService:
    """
    This class is responsible for managing & authenticating user operations that do not fit in the REST API endpoints
    (because they require more complex logic, or short-term statefullness like social login etc)
    """
    def __init__(self):
        self._log = logging.getLogger(__name__)
        pass


    def get_user(self, username=None, user_id=None) -> Optional['UserProfile']:
        """
        Get user by username or user_id
        :param username: The username of the user
        :param user_id: The user_id of the user
        :return: The userProfile object, or None if not found
        """
        if user_id is not None:
            return db.session.execute(db.select(UserProfile).where(UserProfile.id == user_id)).scalar_one_or_none()
        elif username is not None:
            return db.session.execute(db.select(UserProfile).where(UserProfile.username == username)).scalar_one_or_none()
        raise ValueError('Either username or user_id must be provided')


    def authenticate_password(self, username, password) -> 'UserProfile':
        """
        Authenticate the user using username and password
        :param username: The username of the user
        :param password: The password of the user
        :raise RuntimeError: If the user is not found, the password is incorrect or the user uses OAuth2
        :return: The userProfile object, or None if not found or failed to authenticate
        """
        user: Optional['UserProfile'] = self.get_user(username=username)
        if user is None:
            self._log.debug(f'User {username} not found, cannot authenticate')
            raise RuntimeError('User not found')

        # check if the found user doesn't use OAuth2
        if user.uses_oauth2():
            self._log.debug(f'User {username} uses OAuth2, cannot authenticate')
            raise RuntimeError("You're trying to login using a password, but this account uses OAuth2. Please use the OAuth2 (Google) button instead.")

        pwd_match = user.credentials.authenticate({'username': username, 'password': password})
        if not pwd_match:
            self._log.info(f'User {username} provided wrong password, cannot authenticate')
            raise RuntimeError('Invalid password')

        self._log.info(f'User {username} authenticated successfully')
        return user


    def create_jwt(self, user: 'UserProfile') -> str:
        """
        Generate a JWT token for the user.
        Tokens are identified by the user_id
        ONLY use this method after successful authentication
        :param user: The user to generate the token for
        :return: The JWT token
        """
        self._log.debug(f'Generating JWT token for user {user.id}')
        token = create_access_token(identity=user.id)
        return token


    def create_user_password(self, username: str, password: str, firstname: str, lastname: str) -> 'UserProfile':
        """
        Create a new user with a password
        The username should not be already be taken. Check in advance with get_user()
        :param lastname:  The last name
        :param firstname: The first name
        :param username: The username of the user
        :param password: The password of the user, plaintext
        :return: The new user object
        """
        credentials: Credentials = PasswordCredentials.create_from_password(password)
        return self.create_user(credentials, username, firstname, lastname)


    def create_user(self, credentials: 'Credentials', username: str, firstname: str, lastname: str) -> 'UserProfile':
        """
        Create a new user with a password
        The username should not be already be taken. Check in advance with get_user()
        :param username: The username of the user
        :param lastname:  The last name
        :param firstname: The first name
        :param credentials: The credentials object
        :return: The new user object
        """
        assert self.get_user(username) is None, f'User {username} already exists'
        self._log.info(f'Creating new account for {firstname} {lastname} with username {username}')
        user: UserProfile = UserProfile(username, firstname, lastname, credentials)
        current_app.db.session.add(user)

        # Create island for the user
        user.player = self.setup_player(user.player)
        current_app.db.session.commit()
        return user


    def create_user_oauth2(self, sso_id:str, username: str, firstname: str, lastname: str) -> 'UserProfile':
        """
        Create a new user with a password
        The username should not be already be taken. Check in advance with get_user()
        :param sso_id: The OAuth2 ID of the user. This should be unique for each user of the same OAuth2 provider
        :param username: The username of the user
        :param lastname:  The last name
        :param firstname: The first name
        :return: The new user object
        """
        credentials: Credentials = OAuth2Credentials(sso_id)
        return self.create_user(credentials, username, firstname, lastname)

    def setup_player(self, player: 'Player') -> 'Player':
        """
        Create a new island for the given player
        This will also create all objects that are required for the island
        :param player: The player to create the island for
        :return: The new island
        """
        # Create the island without the altar linked
        island = Island(player)
        current_app.db.session.add(island)
        current_app.db.session.commit()

        # Create a new altar building
        altar_building = AltarBuilding(island_id=island.owner_id, x=0, z=0, level=1)
        current_app.db.session.add(altar_building)
        current_app.db.session.commit()

        # Create first mine building
        mine_building = MineBuilding(island_id=island.owner_id, x=1, z=0, level=1)
        current_app.db.session.add(mine_building)
        current_app.db.session.commit()

        # Create update the id of the altar in island so we have a ref from island to altar
        island.altar_id = altar_building.placeable_id
        current_app.db.session.commit()

        # Create the player entity
        player_entity = PlayerEntity(player_id=player.user_profile_id, island_id=island.owner_id, xpos=0, zpos=0, ypos=0, level=1)
        player_entity.update({'level': 1, 'x': 0, 'z': 15, 'y': 0})
        player_entity.player = player
        player.entity = player_entity
        current_app.db.session.add(player_entity)
        current_app.db.session.commit()

        # Create the stats object for the player
        player_stats = PlayerStats(player_id=player.user_profile_id)
        current_app.db.session.add(player_stats)
        current_app.db.session.commit()

        # player settings
        settings = UserSettings(player_id=player.user_profile_id)
        # other default settings are set by the db
        current_app.db.session.add(settings)
        current_app.db.session.commit()

        # The player can initially only build the altar
        player.update({'blueprints': [BlueprintType.ALTAR.value]})

        # Update player spells, it initially has the build spell
        from src.model.spell import Spell
        for i, spell in enumerate(Spell.query.all()):
            player.spells_association.append(PlayerSpellAssociation(player_id=player.user_profile_id, spell_id=spell.id, slot=0 if i == 0 else None))

        current_app.db.session.commit()

        return player

    def update_last_login(self, user: 'UserProfile') -> None:
        """
        Update the last login of the user
        :param user: The user to update
        :return: None
        """
        user.update({'last_login': current_app.db.func.now()})
        current_app.db.session.commit()


AUTH_SERVICE = AuthService()