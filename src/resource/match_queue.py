import logging

from flask import request

from flask import current_app

from src.model.player_entity import PlayerEntity
from src.model.match_queue import MatchQueueEntry
from src.schema import ErrorSchema, SuccessSchema

from flask import Flask, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.model.player import Player
from typing import Optional
from markupsafe import escape
from flask_restful_swagger_3 import Resource, swagger, Api

from src.resource import add_swagger, clean_dict_input, check_data_ownership
from src.swagger_patches import Schema, summary

class MatchQueueSchema(Schema):
    """
    The schema for the endpoint's requests & responses
    """

    properties = {
        'matchmake': {
            'type': 'boolean',
            'description': 'whether wants to start matchmaking or stop it'
        }
    }

    required = ['matchmake']
    type = 'object'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MatchQueueResource(Resource):
    """
    Resource for the match queue endpoint
    There's no POST method because the match queue is a shared resource and players can only be added or removed from it
    The delete endpoint has the same functionality as the put endpoint, but with matchmake set to False
    """


    @swagger.tags('match queue')
    @summary('join the matchmaking queue for multiplayer')
    @swagger.expected(schema=MatchQueueSchema, required=True)
    @swagger.parameter(name='player_id', description='The target player to add / remove from the queue. Should only be used by admins', _in='query', schema={'type': 'integer'}, required=False)
    @swagger.response(200, 'Success', schema=MatchQueueSchema)
    @swagger.response(400, 'Invalid input', schema=ErrorSchema)
    @swagger.response(404, 'player not found', schema=ErrorSchema)
    @swagger.response(409, 'player already / not in the queue', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not the target user (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        add player to the matchmaking queue and test whether 2 players can be matched, send a message to the matched players via websocket
        """

        current_user_id = get_jwt_identity()

        data = request.get_json()
        data = clean_dict_input(data)

        target_user_id = int(escape(request.args.get('player_id', current_user_id)))

        target_player: Optional[Player] = Player.query.get(target_user_id)
        if not target_player:
            return ErrorSchema(f"Player {target_user_id} not found"), 404

        r = check_data_ownership(target_user_id)  # Check the target player is the one invoking it - only admins can add other players
        if r: return r

        try:
            # Validate the input
            MatchQueueSchema(**data, _check_requirements=True)
        except ValueError as e:
            return ErrorSchema(str(e)), 400


        add_to_queue = data['matchmake']
        entry = MatchQueueEntry.query.filter_by(player_id=target_user_id).first()


        if add_to_queue:
            if entry is not None:
                return ErrorSchema(f"Player {target_user_id} already in the queue"), 409

            # First check if there's an opponent in the queue
            # If there is, remove both players from the queue and start the match by sending a message to both players through the websocket
            # If there isn't, add the player to the queue

            # Check for opponents
            diff: int = 1 if 'APP_MATCHMAKING_LEVEL_RANGE' not in current_app.config else int(current_app.config.get('APP_MATCHMAKING_LEVEL_RANGE'))

            entry: Optional[MatchQueueEntry] = MatchQueueEntry.query\
                        .join(Player) \
                        .join(PlayerEntity) \
                        .filter(MatchQueueEntry.player_id != target_user_id) \
                        .filter(target_player.entity.level - diff <= PlayerEntity.level)\
                        .filter(PlayerEntity.level <= target_player.entity.level + diff) \
                        .first()

            if entry is not None:
                opponent: Player = entry.player
                # Remove the entry (not player!) from the queue
                current_app.db.session.delete(entry)
                current_app.db.session.commit()

                # Send a message to the players through the websocket
                current_app.socketio.forwarding_namespace.on_match_found(target_user_id, opponent.user_profile_id)

                logging.getLogger(__name__).info(f"Match found between {target_user_id} (level={target_player.entity.level}) and {opponent.user_profile_id} (level={opponent.entity.level})")
                return MatchQueueSchema(matchmake=True), 200

            else:
                # Add the player to the queue
                entry = MatchQueueEntry(player_id=target_user_id)
                current_app.db.session.add(entry)
                current_app.db.session.commit()
                logging.getLogger(__name__).info(f"Player {target_user_id} added to the queue")
                return MatchQueueSchema(matchmake=True), 200



        else:
            if entry is None:
                return ErrorSchema(f"Player {target_user_id} not in the queue"), 409
            current_app.db.session.delete(entry)
            current_app.db.session.commit()
            return MatchQueueSchema(matchmake=False), 200



    @swagger.tags('match queue')
    @summary('leave the matchmaking queue for multiplayer')
    @swagger.expected(schema=MatchQueueSchema, required=True)
    @swagger.parameter(name='id', description='The target player to remove from the queue', _in='query', schema={'type': 'integer'}, required=False)
    @swagger.response(200, 'Success', schema=SuccessSchema)
    @swagger.response(400, 'Invalid input', schema=ErrorSchema)
    @swagger.response(404, 'player not found', schema=ErrorSchema)
    @swagger.response(409, 'player not in the queue', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def delete(self):
        """
        remove player from the matchmaking queue
        """

        current_user_id = get_jwt_identity()

        data = request.get_json()
        data = clean_dict_input(data)

        target_user_id = int(escape(request.args.get('id', current_user_id)))

        player: Optional[Player] = Player.query.get(target_user_id)
        if not player:
            return ErrorSchema(f"Player {target_user_id} not found"), 404

        r = check_data_ownership(target_user_id)  # Check the target player is the one invoking it - only admins can remove other players
        if r: return r

        try:
            # Validate the input
            MatchQueueSchema(**data, _check_requirements=True)
        except ValueError as e:
            return ErrorSchema(str(e)), 400

        entry = MatchQueueEntry.query.filter_by(player_id=target_user_id).first()
        if entry is None:
            return ErrorSchema(f"Player {target_user_id} not in the queue"), 409
        current_app.db.session.delete(entry)
        current_app.db.session.commit()
        return SuccessSchema(f"Player {target_user_id} succesfully removed from the matchmaking queue."), 200



def attach_resource(app: Flask) -> None:
    """
    Attach the MatchQueue (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_matchmaking', __name__)
    api = Api(blueprint)
    api.add_resource(MatchQueueResource, '/api/matchmaking')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)