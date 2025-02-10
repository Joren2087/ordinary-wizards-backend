import sqlalchemy
from flask import request, current_app, Blueprint, Flask
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.model.player_stats import PlayerStats
from src.resource import clean_dict_input, add_swagger
from src.schema import ErrorSchema
from src.swagger_patches import Schema, summary


class PlayerStatsSchema(Schema):
    """
    JSON Schema for the player statistics
    """

    properties = {
        'player_id': {
            'type': 'integer',
            'format': 'int64'
        },
        'player_kills': {
            'type': 'integer',
            'format': 'int64'
        },
        'player_deaths': {
            'type': 'integer',
            'format': 'int64'
        },
        'minions_killed': {
            'type': 'integer',
            'format': 'int64'
        },
        'damage_dealt': {
            'type': 'integer',
            'format': 'int64'
        },
        'damage_taken': {
            'type': 'integer',
            'format': 'int64'
        },
        'mana_spent': {
            'type': 'integer',
            'format': 'int64'
        },
        'spell_casts': {
            'type': 'integer',
            'format': 'int64'
        },
        'gems_won': {
            'type': 'integer',
            'format': 'int64'
        },
        'gems_lost': {
            'type': 'integer',
            'format': 'int64'
        },
        'games_played': {
            'type': 'integer',
            'format': 'int64'
        },
        'games_won': {
            'type': 'integer',
            'format': 'int64'
        }
    }

    required = ['player_id']

    def __init__(self, player_stats: PlayerStats = None, **kwargs):
        if player_stats is not None:
            super().__init__(
                player_id=player_stats.player_id,
                player_kills=player_stats.player_kills,
                player_deaths=player_stats.player_deaths,
                minions_killed=player_stats.minions_killed,
                damage_dealt=player_stats.damage_dealt,
                damage_taken=player_stats.damage_taken,
                mana_spent=player_stats.mana_spent,
                spell_casts=player_stats.spell_casts,
                gems_won=player_stats.gems_won,
                gems_lost=player_stats.gems_lost,
                games_played=player_stats.games_played,
                games_won=player_stats.games_won,
                **kwargs
            )
        else:
            super().__init__(**kwargs)


class PlayerStatsResource(Resource):
    """
    Endpoint for multiplayer statistics of a player
    It has a weak relationship with the player model, thus no POST and DELETE methods are implemented
    """

    @swagger.tags('stats')
    @summary('Get the statistics of a player')
    @swagger.parameter(name='player_id', description='The id of the player', required=True, _in='query', schema={'type': 'integer'})
    @swagger.response(response_code=200, description='The statistics of the player', schema=PlayerStatsSchema)
    @swagger.response(response_code=400, description='Invalid input', schema=ErrorSchema)
    @swagger.response(response_code=404, description='The player does not exist', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Get the statistics of a player
        :return: The statistics of the player
        """
        player_id = request.args.get('player_id', type=int)
        if not player_id:
            return ErrorSchema("Invalid player_id"), 400

        player_stats = PlayerStats.query.get(player_id)
        if player_stats is None:
            return ErrorSchema("Player not found"), 404
        return PlayerStatsSchema(player_stats), 200


    @swagger.tags('stats')
    @summary('Update the statistics of a player')
    @swagger.expected(schema=PlayerStatsSchema, required=True)
    @swagger.response(response_code=200, description='Success, returns the updated statistics of the player', schema=PlayerStatsSchema)
    @swagger.response(response_code=400, description='Invalid input', schema=ErrorSchema)
    @swagger.response(response_code=404, description='The player does not exist', schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update the statistics of a player
        :return: The updated statistics of the player
        """
        data = request.get_json()
        data = clean_dict_input(data)
        try:
            PlayerStatsSchema(**data, _check_requirements=False)

            player_id = data.get('player_id')
            player_stats = PlayerStats.query.get(player_id)
            if player_stats is None:
                return ErrorSchema("Player not found"), 404

            player_stats.update(data)
            current_app.db.session.commit()

            return PlayerStatsSchema(player_stats), 200

        except ValueError as e:
            return ErrorSchema(str(e)), 400
        except sqlalchemy.exc.IntegrityError as e:
            return ErrorSchema(str(e.orig)), 400


def attach_resource(app: Flask):
    """
    Attach the PlayerStatsResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_stats', __name__)
    api = Api(blueprint)
    api.add_resource(PlayerStatsResource, '/api/player_stats')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)

