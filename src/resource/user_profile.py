import logging

from flask import Flask, Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful_swagger_3 import Resource, swagger, Api
from markupsafe import escape

from src.schema import ErrorSchema, SuccessSchema
from src.resource import add_swagger, clean_dict_input
from src.service.auth_service import AUTH_SERVICE
from src.swagger_patches import Schema, summary


class UserProfileSchema(Schema):
    """
    The schema for the user profile response
    """
    type = 'object'
    properties = {
        'id': {
            'type': 'integer'
        },
        'username': {
            'type': 'string'
        },
        'firstname': {
            'type': 'string'
        },
        'lastname': {
            'type': 'string'
        },
        'admin': {
            'type': 'bool'
        }
    }

    required = ['id', 'username', 'firstname', 'lastname', 'admin']

    def __init__(self, user = None, **kwargs):
        if user is not None:
            super().__init__(id=user.id, username=user.username, firstname=user.firstname,
                         lastname=user.lastname, admin=user.admin, **kwargs)
        else:
            super().__init__(**kwargs)



class UserProfileResource(Resource):
    """
    A UserProfile resource is a resource/api endpoint that allows for the retrieval and modification of user profiles
    No POST endpoint is available, as user profiles are created by the registration process. See AUTHENTICATION.md for more information
    This resource is protected by JWT, and requires a valid JWT token to access
    """

    @swagger.tags('user_profile')
    @summary('Retrieve the user profile with the given id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The user profile id to retrieve. Defaults to the current user id (by JWT)')
    @swagger.response(200, description='Success, returns the user profile in JSON format', schema=UserProfileSchema)
    @swagger.response(403, description='Attempted access to other user profile (while not admin)', schema=ErrorSchema)
    @swagger.response(404, description='Unknown user id', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Get the user profile by id
        Defaults to the current user id (by JWT)
        :return: The user profile in JSON format
        """
        current_user = get_jwt_identity()
        target_user_id = int(escape(request.args.get('id', current_user)))
        invoker_user = AUTH_SERVICE.get_user(user_id=current_user)

        if not invoker_user or (current_user != target_user_id and not invoker_user.admin):
            logging.getLogger(__name__).warning(f'User {current_user} attempted to access user {request.args.get("id")}, not authorized')
            return ErrorSchema(f"Access denied to profile {target_user_id}"), 403

        # Get the user profile
        if target_user_id != current_user:
            # users differ, so we're going to get the profile of the requested user
            target_user = AUTH_SERVICE.get_user(user_id=target_user_id)
        else:
            # The invoker is modifying his own profile
            target_user = invoker_user


        if target_user is None:
            return ErrorSchema(f"User {target_user_id} not found"), 404
        else:
            return UserProfileSchema(target_user), 200


    @swagger.tags('user_profile')
    @summary('Update the user profile by id. Note that id is here NOT required, but can be used to update other user profiles (if the invoker is an admin). Updateable fields are firstname, lastname & admin')
    @swagger.expected(UserProfileSchema, required=True)
    @swagger.response(200, description='Succesfully updated the user profile', schema=UserProfileSchema)
    @swagger.response(403, description='Attempted access to other user profile (while not admin), attempt to set the admin property (while not admin) or invalid JWT token', schema=ErrorSchema)
    @swagger.response(404, description='Unknown user id', schema=ErrorSchema)
    @swagger.response(400, description='Invalid input', schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update the user profile by id
        Defaults to the current user id (by JWT)
        Allowed parameters to update: firstname, lastname
        :return:
        """
        data = request.get_json()
        data = clean_dict_input(data)
        try:
            UserProfileSchema(**data, _check_requirements=False)  # Validate the input

            current_user = get_jwt_identity()
            target_user_id = int(data['id'] if 'id' in data else current_user)
            invoker_user = AUTH_SERVICE.get_user(user_id=current_user)
            if not invoker_user:
                logging.getLogger(__name__).warning(f'User {current_user} does not exist, but this id comes from his JWT token. Is the token invalid or did his account just got deleted?')
                return ErrorSchema(f"Current user does not exist. Is your JWT token invalid? Or did your account just got deleted?"), 404

            if current_user != target_user_id and not invoker_user.admin:
                logging.getLogger(__name__).warning(
                    f'User {current_user} attempted to access user {request.args.get("id")}, not authorized')
                return ErrorSchema(f"Access denied to profile {target_user_id}"), 403

            # Get the user profile
            if target_user_id != current_user:
                # users differ, so we're going to get the profile of the requested user
                target_user = AUTH_SERVICE.get_user(user_id=target_user_id)
            else:
                # The invoker is modifying his own profile
                target_user = invoker_user

            if target_user is None:
                return ErrorSchema(f"User {target_user_id} not found"), 404

            if 'admin' in data:
                # Check if the current user is an admin, otherwise he's not allowed to change the admin bit
                # (a creative user would be able to give himself admin, so we need to check this)
                if not invoker_user.admin:
                    return ErrorSchema(f"Access denied to set admin status for profile {target_user_id}"), 403

            target_user.update(data)
            current_app.db.session.commit()  # Save changes to db

            return UserProfileSchema(target_user), 200


        except (ValueError, KeyError) as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('user_profile')
    @summary('Delete the user profile by id. Id defautls to the current user id (by JWT)')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The user profile id to delete. Defaults to the current user id (by JWT)')
    @swagger.response(200, description='Success, user profile has been deleted', schema=SuccessSchema)
    @swagger.response(403, description='Attempted access to other user profile (while not admin) or invalid JWT token', schema=ErrorSchema)
    @swagger.response(404, description='Unknown user id', schema=ErrorSchema)
    @jwt_required()
    def delete(self):
        """
        Delete the user profile by id
        Defaults to the current user id (by JWT)
        :return: Success message
        """
        current_user = get_jwt_identity()
        target_user_id = int(escape(request.args.get('id', current_user)))
        invoker_user = AUTH_SERVICE.get_user(user_id=current_user)
        if not invoker_user:
            logging.getLogger(__name__).warning(f'User {current_user} does not exist, but this id comes from his JWT token. Is the token invalid or did his account just got deleted?')
            return ErrorSchema(f"Current user {current_user} does not exist. Is your JWT token invalid? Or did your account just got deleted?"), 400

        if current_user != target_user_id and not invoker_user.admin:
            logging.getLogger(__name__).warning(f'User {current_user} attempted to access user {request.args.get("id")}, not authorized')
            return ErrorSchema(f"Access denied to profile {target_user_id}"), 403

        # Get the user profile
        if target_user_id != current_user:
            # users differ, so we're going to get the profile of the requested user
            target_user = AUTH_SERVICE.get_user(user_id=target_user_id)
        else:
            # The invoker is modifying his own profile
            target_user = invoker_user

        if target_user is None:
            return ErrorSchema(f"User {target_user_id} not found"), 404
        else:
            logging.getLogger(__name__).info(f'Annihilating user {target_user_id} from existence... (deleting user profile)')
            current_app.db.session.delete(target_user)
            current_app.db.session.commit()
            return SuccessSchema(f"User {target_user_id} has been deleted"), 200






def attach_resource(app: Flask) -> None:
    """
    Attach the UserProfileResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_user_profile', __name__)
    api = Api(blueprint)
    api.add_resource(UserProfileResource, '/api/user_profile')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)


