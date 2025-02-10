from flask import request, Flask, Blueprint
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.model.chat_message import ChatMessage
from src.resource import add_swagger
from src.schema import ErrorSchema
from src.swagger_patches import Schema, summary

class ChatMessageSchema(Schema):
    """
    The schema for the chat message
    """
    type = 'object'
    properties = {
        'id': {
            'type': 'integer',
            'description': 'The unique identifier of the chat message'
        },
        'user_id': {
            'type': 'integer',
            'description': 'The unique identifier of the user profile that sent the message'
        },
        'message': {
            'type': 'string',
            'description': 'The message content'
        },
        'created_at': {
            'type': 'date-time',
            'description': 'The timestamp when the message was sent'
        }
    }

    required = ['user_id', 'message']

    description = 'The chat message - represents a message sent by a user in the chat'

    def __init__(self, chat_message: ChatMessage =None, **kwargs):
        if chat_message is not None:
            super().__init__(
                             id=chat_message.id,
                             user_id=chat_message.user_id,
                             message=chat_message.message,
                             created_at=str(chat_message.created_at).replace(' ', 'T'),
                             **kwargs)
        else:
            super().__init__(**kwargs)


class ChatMessageResource(Resource):
    """
    The resource for chat messages
    Only a GET method is implemented, as chat messages are send/posted through the chat websocket
    Updating / altering of chat messages is not allowed and therefore not implemented
    """

    @swagger.tags('chat')
    @summary('Get chat message by id')
    @swagger.parameter(name='id', description='The unique identifier of the chat message', required=True, _in='query', schema={'type': 'integer'})
    @swagger.response(200, 'Success', schema=ChatMessageSchema)
    @swagger.response(404, 'Chat message not found', schema=ErrorSchema)
    @swagger.response(400, 'Invalid request', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Get a chat message by id
        :return: The chat message
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema('Chat id missing'), 400

        chat_message = ChatMessage.query.get(id)
        if chat_message is None:
            return ErrorSchema('Chat message not found'), 404

        return ChatMessageSchema(chat_message), 200


class ChatMessageListResource(Resource):
    """
    Resource for listing of chat messages, eg all chat messages of a user
    """

    @swagger.tags('chat')
    @summary('List chat messages of a player')
    @swagger.parameter(name='user_id', description='The unique identifier of the user profile', required=True, _in='query', schema={'type': 'integer'})
    @swagger.response(200, 'Success', schema=ChatMessageSchema)
    @swagger.response(404, 'No user and/or chat messages found', schema=ErrorSchema)
    @swagger.response(400, 'Invalid request', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        List all chat messages of a player
        :return: The chat messages
        """
        user_id = request.args.get('user_id', type=int)
        if user_id is None:
            return ErrorSchema('User id missing'), 400

        chat_messages = ChatMessage.query.filter_by(user_id=user_id).all()
        if not chat_messages:
            return ErrorSchema('No user and/or chat messages found'), 404

        return [ChatMessageSchema(chat_message) for chat_message in chat_messages], 200



def attach_resources(app: Flask):
    """
    Attach the ChatMessageListResource and ChatMessageResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_chat_message', __name__)
    api = Api(blueprint)
    api.add_resource(ChatMessageResource, '/api/chat_message')
    api.add_resource(ChatMessageListResource, '/api/chat_message/list')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)



