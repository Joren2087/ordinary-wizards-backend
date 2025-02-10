import logging

from flask import request, current_app, Flask, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful_swagger_3 import Resource, swagger, Api

from src.model.player import Player
from src.model.friend_request import FriendRequest
from src.resource import clean_dict_input, add_swagger, check_data_ownership
from src.schema import ErrorSchema
from src.swagger_patches import Schema, summary

class FriendRequestSchema(Schema):
    """
    The schema for the friend request model when used in RESTful API
    """

    properties = {
        'id': {
            'type': 'integer',
            'format': 'int64'
        },
        'sender_id': {
            'type': 'integer',
            'format': 'int64',
            'description': 'The id of the player that sent the friend request. Defaults to the invoking player if not given.'
        },
        'receiver_id': {
            'type': 'integer',
            'format': 'int64'
        },
        'status': {
            'type': 'string',
            'description': 'The status of the friend request. Can be "pending", "accepted" or "rejected"'
        }
    }

    required = ['receiver_id']

    description = 'The friend request model. A friend request is sent by one player to another to become friends.'

    def __init__(self, friend_request: FriendRequest = None, status: str = 'pending', **kwargs):
        if friend_request:
            super().__init__(id=friend_request.id,
                             sender_id=friend_request.sender_id,
                             receiver_id=friend_request.receiver_id,
                             status=status, # This is always pending, because if it would be accepted or rejected, it would be deleted
                             **kwargs)
        else:
            super().__init__(**kwargs)


class FriendRequestResource(Resource):
    """
    A resource / api endpoint that allows for the retrieval and modification of friend requests
    """

    @swagger.tags('friend request')
    @summary('Get a friend request by id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The id of the friend request to retrieve', required=True)
    @swagger.response(response_code=200, description='Successful retrieval', schema=FriendRequestSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @swagger.response(response_code=404, description='Friend request not found', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve the friend request with the given id
        The id of the friend request to retrieve is given as a query parameter
        :return: The friend request in JSON format
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema('No id given'), 400

        friend_request = FriendRequest.query.get(id)
        if friend_request is None:
            return ErrorSchema('Friend request not found'), 404

        return FriendRequestSchema(friend_request), 200


    @swagger.tags('friend request')
    @summary('Create a new friend request')
    @swagger.expected(schema=FriendRequestSchema, required=True)
    @swagger.response(response_code=200, description='Friend request created', schema=FriendRequestSchema)
    @swagger.response(response_code=400, description='Invalid input', schema=ErrorSchema)
    @swagger.response(response_code=404, description='Sender or receiver not found', schema=ErrorSchema)
    @swagger.response(response_code=409, description='Friend request already exists or sender & reciever are already friends', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not the sender of the friend request (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def post(self):
        """
        Create a new friend request
        :return: The friend request in JSON format
        """
        data = request.get_json()
        data = clean_dict_input(data)

        if 'status' in data:
            data.pop('status')  # Status is always pending when creating a friend request, it should be used in PUT
        if 'id' in data:
            data.pop('id')

        try:
            FriendRequestSchema(**data, _check_requirements=True)
        except ValueError as e:
            return ErrorSchema(str(e)), 400

        if not 'sender_id' in data:
            data['sender_id'] = get_jwt_identity()

        if data['sender_id'] == data['receiver_id']:
            return ErrorSchema('Feeling lonely huh? (Sender and receiver cannot be the same player)'), 400

        # Check if the sender and receiver exist
        sender: Player = current_app.db.session.query(Player).get(int(data['sender_id']))
        receiver: Player = current_app.db.session.query(Player).get(int(data['receiver_id']))

        r = check_data_ownership(sender.user_profile_id)  # Only the sender can send a friend request to someone else
        if r: return r

        if sender is None:
            return ErrorSchema(f"Sender {data['sender_id']} not found"), 404
        if receiver is None:
            return ErrorSchema(f"Receiver {data['receiver_id']} not found"), 404

        # Check if they are already friends
        if receiver in sender.friends:
            return ErrorSchema(f"{sender.user_profile_id} and {receiver.user_profile_id} are already friends"), 409

        # Check if the friend request already exists
        req: FriendRequest = current_app.db.session.query(FriendRequest) \
               .filter_by(sender_id=sender.user_profile_id, receiver_id=receiver.user_profile_id) \
               .first()
        if req is not None:
            return ErrorSchema(f'Friend request from {sender.user_profile_id} to {receiver.user_profile_id} already exists as friend request {req.id}'), 409

        friend_request = FriendRequest(sender=sender, receiver=receiver)
        current_app.db.session.add(friend_request)
        current_app.db.session.commit()

        return FriendRequestSchema(friend_request), 200


    @swagger.tags('friend request')
    @summary('Update a friend request by id. Only the status field is updateable. Can be "pending" (do nothing), "accepted" (add as friend and remove FR) or "rejected" (remove FR)')
    @swagger.expected(schema=FriendRequestSchema, required=True)
    @swagger.response(response_code=200, description='Friend request updated', schema=FriendRequestSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @swagger.response(response_code=404, description='Friend request not found', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not the receiver of the friend request (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update a friend request by id
        :return: The friend request in JSON format
        """
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            FriendRequestSchema(**data, _check_requirements=False)
            id = int(data['id'])

            friend_request = FriendRequest.query.get(id)
            if friend_request is None:
                return ErrorSchema(f'Friend request {id} not found'), 404

            r = check_data_ownership(friend_request.receiver_id)  # Only the receiver can accept or reject the friend request
            if r: return r

            if 'status' in data:
                if data['status'] == 'accepted':
                    logging.debug(f"Accepting friend request {friend_request.id} ({friend_request.sender_id} -> {friend_request.receiver_id})")
                    # Add the sender and receiver as friends
                    friend_request.sender.friends.append(friend_request.receiver)
                    friend_request.receiver.friends.append(friend_request.sender)
                    current_app.db.session.delete(friend_request)
                    current_app.db.session.commit()
                elif data['status'] == 'rejected':
                    logging.debug(f"Rejecting friend request {friend_request.id} ({friend_request.sender_id} -> {friend_request.receiver_id})")
                    current_app.db.session.delete(friend_request)
                    current_app.db.session.commit()

                # If the status is pending, do nothing

            return FriendRequestSchema(friend_request, status=data['status']), 200

        except (ValueError, TypeError) as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('friend request')
    @summary('Delete (=reject) a friend request by id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The id of the friend request to delete', required=True)
    @swagger.response(response_code=200, description='Friend request deleted', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @swagger.response(response_code=404, description='Friend request not found', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not the receiver of the friend request (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def delete(self):
        """
        Delete a friend request by id
        :return: The success message, or an error message
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema('No id given'), 400

        friend_request = FriendRequest.query.get(id)
        if friend_request is None:
            return ErrorSchema('Friend request not found'), 404

        r = check_data_ownership(
            friend_request.receiver_id)  # Only the receiver can accept or reject the friend request
        if r: return r

        current_app.db.session.delete(friend_request)
        current_app.db.session.commit()

        return ErrorSchema('Friend request deleted'), 200


class FriendRequestListResource(Resource):
    """
    A resource / api endpoint that allows for the retrieval of multiple friend requests
    """

    @swagger.tags('friend request')
    @summary('Get all friend requests to a player')
    @swagger.parameter(_in='query', name='receiver_id', schema={'type': 'int'}, description='The id of the player to get friend requests for', required=True)
    @swagger.response(response_code=200, description='Successful retrieval', schema=FriendRequestSchema)
    @swagger.response(response_code=400, description='No player id', schema=ErrorSchema)
    @swagger.response(response_code=404, description='Player not found', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve all friend requests
        :return: The friend requests in JSON format
        """
        receiver_id = request.args.get('receiver_id', type=int)
        if receiver_id is None:
            return ErrorSchema('No receiver id'), 400

        friend_requests = FriendRequest.query.filter_by(receiver_id=receiver_id).all()
        return [FriendRequestSchema(friend_request) for friend_request in friend_requests], 200



def attach_resource(app: Flask) -> None:
    """
    Attach this resource to the Flask app
    :param app: The Flask app
    """

    blueprint = Blueprint('api_friend_request', __name__)
    api = Api(blueprint)
    api.add_resource(FriendRequestResource, '/api/friend_request')
    api.add_resource(FriendRequestListResource, '/api/friend_request/list')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)
