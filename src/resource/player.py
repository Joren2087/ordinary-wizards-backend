import datetime
from typing import Optional

from flask import current_app, Blueprint, request, Flask
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful_swagger_3 import Resource, swagger, Api
from markupsafe import escape

from src.model.player_entity import PlayerEntity
from src.resource.entity import EntitySchema
from src.resource.gems import GemSchema
from src.swagger_patches import Schema, summary
from src.schema import ErrorSchema, SuccessSchema, IntArraySchema
from src.model.player import Player, PlayerSpellAssociation
from src.resource import add_swagger, clean_dict_input, check_data_ownership

"""
This module contains the PlayerResource, which is a resource/api endpoint that allows for the retrieval and modification of player profiles
The PlayerSchema is used to define the JSON response for the player profile, used in the PlayerResource
"""

class PlayerEntitySchema(EntitySchema):
    """
    The schema for the player entity
    """
    type = 'object'
    properties = {
        'player_id': {
            'type': 'integer'
        }
    }

    required = []

    description = 'The player entity - represents a player in the physical world'

    def __init__(self, player: PlayerEntity = None, **kwargs):
        if player is not None:
            super().__init__(player,
                             player_id=player.player_id,
                             **kwargs)
        else:
            super().__init__(**kwargs)


class PlayerSpellAssociationSchema(Schema):
    """
    The schema for the player spell association
    """
    type = 'object'
    properties = {
        'player_id': {
            'type': 'integer',
            'description': 'The player id'
        },
        'spell_id': {
            'type': 'integer',
            'description': 'The spell id'
        },
        'slot': {
            'type': 'integer',
            'description': 'The slot in which the spell is stored (0-5)'
        }
    }

    required = ['player_id', 'spell_id']

    description = 'The association between a player and a spell'

    def __init__(self, player_spell: PlayerSpellAssociation = None, **kwargs):
        if player_spell is not None:
            super().__init__(player_id=player_spell.player_id,
                             spell_id=player_spell.spell_id,
                             slot=player_spell.slot,
                             **kwargs)
        else:
            super().__init__(**kwargs)


class PlayerSchema(Schema):
    """
    The schema for the player profile requests & responses
    """
    type = 'object'
    properties = {
        'user_profile_id': {
            'type': 'integer',
            'description': 'The unique identifier of the user profile'
        },
        'username': {
            'type': 'string',
            'description': 'The username of the player'
        },
        'crystals': {
            'type': 'integer',
            'description': 'The amount crystals the player has'
        },
        'mana': {
            'type': 'integer',
            'description': 'The amount of mana the player has'
        },
        'xp': {
            'type': 'integer',
            'description': 'The experience points of the player'
        },
        'spells': PlayerSpellAssociationSchema.array(),
        'gems': {
            'type': 'array',
            'description': 'The gem inventory of the player',
            'items': GemSchema
        },
        'entity': PlayerEntitySchema,
        'last_login': {
            'type': 'string',
            'format': 'date-time',
            'description': 'The last login time of the player'
        },
        'last_logout': {
            'type': 'string',
            'format': 'date-time',
            'description': 'The last logout time of the player'
        },
        'friends': IntArraySchema
    }

    required = []  # nothing is required, but not giving anything is just doing nothing

    def __init__(self, player: Player= None, **kwargs):
        if player is not None: # player -> schema
            super().__init__(user_profile_id=player.user_profile_id,
                             crystals=player.crystals, mana=player.mana, xp=player.xp,
                             last_login=str(player.last_login).replace(' ', 'T'),
                             last_logout=str(player.last_logout).replace(' ', 'T'),
                             spells=[PlayerSpellAssociationSchema(assoc) for assoc in player.spells_association],
                             gems=[GemSchema(gem) for gem in player.gems],
                             entity=PlayerEntitySchema(player=player.entity),
                             username=player.user_profile.username,
                             friends=[friend.user_profile_id for friend in player.friends],
                             **kwargs)
        else:  # schema -> player
            super().__init__(**kwargs)




class PlayerResource(Resource):
    """
    A Player resource is a resource/api endpoint that allows for the retrieval and modification of player profiles

    This resource is protected by JWT, and requires a valid JWT token to access
    """

    @swagger.tags('player')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The player profile id to retrieve. Defaults to the current user id (by JWT)')
    @swagger.response(200, description='Success, returns the player profile in JSON format', schema=PlayerSchema)
    @swagger.response(404, description='Unknown player id', schema=ErrorSchema)
    @summary('Get the player profile by id')
    @jwt_required()
    def get(self):
        """
        Get the player profile by id
        Defaults to the current user id (by JWT)
        :return: The player profile in JSON format
        """
        current_user_id = get_jwt_identity()

        target_user_id = int(escape(request.args.get('id', current_user_id)))

        player: Optional[Player] = Player.query.get(target_user_id)

        # Check if the target player exists
        if player is None:
            return ErrorSchema(f"Player {target_user_id} not found"), 404
        else:
            return PlayerSchema(player), 200

    @swagger.tags('player')
    @swagger.expected(PlayerSchema)
    @summary('Update the player profile by id. All fields (except id, gems and username) are updatable. Including entity (and its modifiable fields),'
             ' spells (by ids), blueprints (by ids), friends (by ids), last_login, last_logout, xp, mana and crystals')
    @swagger.response(200, description='Succesfully updated the player profile', schema=PlayerSchema)
    @swagger.response(404, description='Unknown player id', schema=ErrorSchema)
    @swagger.response(403, description='Caller is not owner of the given id', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update the player profile by id
        Defaults to the current user id (by JWT)
        :return: The player profile in JSON format
        """

        data = request.get_json()
        data = clean_dict_input(data)
        try:
            if 'user_profile_id' in data:
                user_id = int(data['user_profile_id'])
                r = check_data_ownership(
                    user_id)  # Check the target player is the one invoking it - only admins can change other players
                if r: return r
            else:
                user_id = get_jwt_identity()


            if 'gems' in data:
                # Gems are not updated directly, but through the gem resource
                data.pop('gems')

            PlayerSchema(**data)  # Validate the input

            # Get the player profile
            player: Optional[Player] = Player.query.get(user_id)

            # Check if the target player exists
            if player is None:  # This should never happen, as the player is guaranteed to exist by the JWT
                return ErrorSchema(f"Player {user_id} not found"), 404

            # Convert the datetime strings to datetime objects
            if 'last_login' in data:
                data['last_login'] = data['last_login'].replace('T', ' ')
                data['last_login'] = data["last_login"].split('.')[0] # Remove fractions of seconds
                data['last_login'] = datetime.datetime.strptime(data['last_login'], '%Y-%m-%d %H:%M:%S')
            if 'last_logout' in data:
                data['last_logout'] = data['last_logout'].replace('T', ' ')
                data['last_logout'] = data["last_logout"].split('.')[0] # Remove fractions of seconds
                data['last_logout'] = datetime.datetime.strptime(data['last_logout'], '%Y-%m-%d %H:%M:%S')

            # Update the player profile, might throw semantic errors as ValueError
            player.update(data)

            current_app.db.session.commit()  # Submit the changes to the database

            return PlayerSchema(player), 200
        except ValueError as e:
            return ErrorSchema(str(e)), 400



class PlayerListResource(Resource):
    """
    A PlayerList resource is a resource/api endpoint that allows for the retrieval of all player profiles
    """

    @swagger.tags('player')
    @summary('Get all player profiles')
    @swagger.response(200, description='Success, returns a list of all player profiles in JSON format', schema=PlayerSchema)
    @jwt_required()
    def get(self):
        """
        Get all player profiles
        :return: The player profiles in JSON format
        """
        players = Player.query.all()
        return [PlayerSchema(player) for player in players], 200


def attach_resource(app: Flask) -> None:
    """
    Attach the PlayerResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_player', __name__)
    api = Api(blueprint)
    api.add_resource(PlayerResource, '/api/player')
    api.add_resource(PlayerListResource, '/api/player/list')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)