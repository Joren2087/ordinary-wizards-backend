from flask import request, Flask, Blueprint, current_app
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.model.user_settings import UserSettings
from src.resource import clean_dict_input, add_swagger, check_data_ownership
from src.schema import ErrorSchema
from src.swagger_patches import Schema, summary


class UserSettingsSchema(Schema):
    """
    JSON Schema for the player settings
    """

    type = 'object'
    properties = {
        'player_id': {
            'type': 'integer',
            'description': 'The id of the player that these settings belong to'
        },
        'audio_volume': {
            'type': 'integer',
            'description': 'The audio volume of the player'
        },
        'performance': {
            'type': 'integer',
            'description': 'The performance setting of the player'
        },
        'selected_cursor': {
            'type': 'integer',
            'description': 'The selected cursor of the player'
        },
        'horz_sensitivity': {
            'type': 'integer',
            'description': 'The horizontal sensitivity of the player'
        },
        'vert_sensitivity': {
            'type': 'integer',
            'description': 'The vertical sensitivity of the player'
        },
        'move_fwd_key': {
            'type': 'string',
            'description': 'The key for moving forward'
        },
        'move_fwd_val': {
            'type': 'string',
            'description': 'The value for moving forward'
        },
        'move_bkwd_key': {
            'type': 'string',
            'description': 'The key for moving backward'
        },
        'move_bkwd_val': {
            'type': 'string',
            'description': 'The value for moving backward'
        },
        'move_left_key': {
            'type': 'string',
            'description': 'The key for moving left'
        },
        'move_left_val': {
            'type': 'string',
            'description': 'The value for moving left'
        },
        'move_right_key': {
            'type': 'string',
            'description': 'The key for moving right'
        },
        'move_right_val': {
            'type': 'string',
            'description': 'The value for moving right'
        },
        'jump_key': {
            'type': 'string',
            'description': 'The key for jumping'
        },
        'jump_val': {
            'type': 'string',
            'description': 'The value for jumping'
        },
        'interact_key': {
            'type': 'string',
            'description': 'The key for interacting'
        },
        'interact_val': {
            'type': 'string',
            'description': 'The value for interacting'
        },
        'eat_key': {
            'type': 'string',
            'description': 'The key for eating'
        },
        'eat_val': {
            'type': 'string',
            'description': 'The value for eating'
        },
        'chat_key': {
            'type': 'string',
            'description': 'The key for chatting'
        },
        'chat_val': {
            'type': 'string',
            'description': 'The value for chatting'
        },
        'slot_1_key': {
            'type': 'string',
            'description': 'The key for slot 1'
        },
        'slot_1_val': {
            'type': 'string',
            'description': 'The value for slot 1'
        },
        'slot_2_key': {
            'type': 'string',
            'description': 'The key for slot 2'
        },
        'slot_2_val': {
            'type': 'string',
            'description': 'The value for slot 2'
        },
        'slot_3_key': {
            'type': 'string',
            'description': 'The key for slot 3'
        },
        'slot_3_val': {
            'type': 'string',
            'description': 'The value for slot 3'
        },
        'slot_4_key': {
            'type': 'string',
            'description': 'The key for slot 4'
        },
        'slot_4_val': {
            'type': 'string',
            'description': 'The value for slot 4'
        },
        'slot_5_key': {
            'type': 'string',
            'description': 'The key for slot 5'
        },
        'slot_5_val': {
            'type': 'string',
            'description': 'The value for slot 5'
        },
        'sprint_key': {
            'type': 'string',
            'description': 'The key for sprinting'
        },
        'sprint_val': {
            'type': 'string',
            'description': 'The value for sprinting'
        }
    }
    required = []

    title = 'UserSettings'
    description = 'A model representing the settings of a player'

    def __init__(self, user_settings: UserSettings = None, **kwargs):
        if user_settings is not None:  # user_settings -> schema
            super().__init__(player_id=user_settings.player_id, audio_volume=user_settings.audio_volume,
                                performance=user_settings.performance, selected_cursor=user_settings.selected_cursor,
                                horz_sensitivity=user_settings.horz_sensitivity, vert_sensitivity=user_settings.vert_sensitivity,
                                move_fwd_key=user_settings.move_fwd_key, move_fwd_val=user_settings.move_fwd_val,
                                move_bkwd_key=user_settings.move_bkwd_key, move_bkwd_val=user_settings.move_bkwd_val,
                                move_left_key=user_settings.move_left_key, move_left_val=user_settings.move_left_val,
                                move_right_key=user_settings.move_right_key, move_right_val=user_settings.move_right_val,
                                jump_key=user_settings.jump_key, jump_val=user_settings.jump_val,
                                interact_key=user_settings.interact_key, interact_val=user_settings.interact_val,
                                eat_key=user_settings.eat_key, eat_val=user_settings.eat_val,
                                chat_key=user_settings.chat_key, chat_val=user_settings.chat_val,
                                slot_1_key=user_settings.slot_1_key, slot_1_val=user_settings.slot_1_val,
                                slot_2_key=user_settings.slot_2_key, slot_2_val=user_settings.slot_2_val,
                                slot_3_key=user_settings.slot_3_key, slot_3_val=user_settings.slot_3_val,
                                slot_4_key=user_settings.slot_4_key, slot_4_val=user_settings.slot_4_val,
                                slot_5_key=user_settings.slot_5_key, slot_5_val=user_settings.slot_5_val,
                                sprint_key=user_settings.sprint_key, sprint_val=user_settings.sprint_val,
                                **kwargs)
        else:  # schema -> user_settings
            super().__init__(**kwargs)



class UserSettingsResource(Resource):

    @swagger.tags('settings')
    @summary('Get the settings of a player')
    @swagger.response(200, description='The settings of the player', schema=UserSettingsSchema)
    @swagger.response(404, description='The player does not exist', schema=ErrorSchema)
    @swagger.parameter(name='player_id', description='The id of the player to get the settings of', required=True, _in='query', schema={'type': 'integer'})
    @swagger.response(400, description='Player id absent', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Get the settings of a player
        :param player_id: The id of the player to get the settings of
        :return: The settings of the player
        """
        id = request.args.get('player_id', type=int)

        if id is None:
            return ErrorSchema('Player id absent'), 400

        user_settings = UserSettings.query.get(id)
        if user_settings is None:
            return ErrorSchema('The player does not exist'), 404

        return UserSettingsSchema(user_settings), 200

    @swagger.tags('settings')
    @summary('Update the settings of a player. All fields (except player_id) are updatable.')
    @swagger.response(200, description='Settings updated', schema=UserSettingsSchema)
    @swagger.response(404, description='The player does not exist', schema=ErrorSchema)
    @swagger.response(400, description='Player id absent', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @swagger.expected(UserSettingsSchema, required=True)
    @jwt_required()
    def put(self):
        """
        Update the settings of a player
        :return: The updated settings of the player
        """

        try:
            data = request.get_json()
            data = clean_dict_input(data)

            UserSettingsSchema(**data, _check_requirements=False)

            id = int(data['player_id'])

            if id is None:
                return ErrorSchema('Player id absent'), 400

            user_settings = UserSettings.query.get(id)
            if user_settings is None:
                return ErrorSchema('The player does not exist'), 404


            data = request.get_json()
            data = clean_dict_input(data)

            r = check_data_ownership(
                user_settings.player_id)  # island_id == owner_id
            if r: return r

            user_settings.update(data)
            current_app.db.session.commit()

            return UserSettingsSchema(user_settings), 200
        except (ValueError, KeyError) as e:
            return str(e), 400


def attach_resource(app: Flask) -> None:
    """
    Attach the PlayerResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_settings', __name__)
    api = Api(blueprint)
    api.add_resource(UserSettingsResource, '/api/settings')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)



