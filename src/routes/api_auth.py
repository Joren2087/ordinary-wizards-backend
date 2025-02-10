import json
import logging
from datetime import datetime, timezone, timedelta

import requests
from flask import Blueprint, current_app, Response, request, redirect
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies, jwt_required, get_jwt, get_jwt_identity, \
    verify_jwt_in_request
from jwt import PyJWTError
from markupsafe import escape
from oauthlib.oauth2 import WebApplicationClient, OAuth2Error

from src.resource import add_endpoint_to_swagger

from src.service.auth_service import AUTH_SERVICE

# Create the blueprint
blueprint = Blueprint('api_auth', __name__)

# Utliity variables
db = current_app.db
_log = logging.getLogger(__name__)

@blueprint.route("/register", methods=['POST'])
def register():
    """
    REST API endpoint for user registration
    Requires username, password, firstname and lastname as query parameters
    :return: Response
    """
    if current_app.config.get('APP_REGISTRATION_ENABLED', 'true') != 'true':
        return Response(json.dumps({'status': 'error', 'message': "Registration not enabled"}), status=409, mimetype='application/json')

    # Check if username and password are provided
    if ('username' not in request.args
            or 'password' not in request.args
            or 'firstname' not in request.args
            or 'lastname' not in request.args):
        return Response(json.dumps({'status': 'error', 'message': 'incorrect number of parameters'}), status=400, mimetype='application/json')

    # Clean input
    username = escape(request.args.get('username'))
    password = escape(request.args.get('password'))
    firstname = escape(request.args.get('firstname'))
    lastname = escape(request.args.get('lastname'))

    # Check if username is already taken
    if AUTH_SERVICE.get_user(username=username) is not None:
        return Response(json.dumps({'status': 'error', 'message': 'username already taken'}), status=409, mimetype='application/json')

    # Create user
    user = AUTH_SERVICE.create_user_password(username, password, firstname, lastname)
    jwt = AUTH_SERVICE.create_jwt(user)

    # Return response
    response = Response(json.dumps({
        'status': 'success',
        'jwt': jwt,
        'ttl': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'user': {
            'id': user.id,
            'firstname': user.firstname,
            'lastname': user.lastname,
            'username': user.username
        }
    }), status=200, mimetype='application/json')

    set_access_cookies(response, jwt, max_age=int(current_app.config.get('APP_JWT_TOKEN_EXPIRES', 3600))) # Set the JWT in the response as a cookie, valid for 1 hour
    return response


@blueprint.route("/login", methods=['POST'])
def login():
    """
    REST API endpoint for user-password login
    Requires username and password as query parameters
    Attempts authentication and returns a JWT token if successful
    If not successful, returns an error message
    :return: Response
    """
    if current_app.config.get('APP_LOGIN_ENABLED', 'true')!= 'true':
        return Response(json.dumps({'status': 'error', 'message': "Login not enabled"}), status=409, mimetype='application/json')

    # Check if username and password are provided
    if 'username' not in request.args or 'password' not in request.args:
        return Response(json.dumps({'status': 'error', 'message': 'username and password not provided'}), status=400, mimetype='application/json')

    # Clean input
    username = escape(request.args.get('username'))
    password = escape(request.args.get('password'))

    # Attempt authentication
    try:
        user = AUTH_SERVICE.authenticate_password(username, password)
    except RuntimeError as e:
        return Response(json.dumps({'status': 'error', 'message': str(e)}), status=401, mimetype='application/json')

    # Generate JWT token
    jwt = AUTH_SERVICE.create_jwt(user)
    AUTH_SERVICE.update_last_login(user)

    # Return response
    response = Response(json.dumps({'status': 'success', 'jwt': jwt, 'ttl': current_app.config['JWT_ACCESS_TOKEN_EXPIRES']}), status=200, mimetype='application/json')
    set_access_cookies(response, jwt, max_age=int(current_app.config.get('APP_JWT_TOKEN_EXPIRES', 3600))) # Set the JWT in the response as a cookie, valid for 1 hour
    return response

@blueprint.route("/logout", methods=['POST', 'GET'])
def logout():
    """
    REST API endpoint for user logout
    Requires a valid JWT token to be provided
    :return: Response
    """
    response = Response(json.dumps({'status': 'success', 'message': 'Logged out'}), status=200, mimetype='application/json')
    unset_jwt_cookies(response) # Unset the JWT in the response as a cookie
    return response


# Do NOT add @jwt_required here as it would completely fuck up the error handling chain, resulting in 500 errors where it's just a 401
@current_app.after_request
def refresh_expiring_jwts(response):
    """
    Checks after each request if the JWT token is about to expire and refreshes it if necessary
    Stolen from https://flask-jwt-extended.readthedocs.io/en/stable/refreshing_tokens/
    :param response: The response to modify (attach the new JWT to)
    :return: The modified response
    """
    try:
        verify_jwt_in_request(optional=True)

        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            _log.debug(f"Refreshing JWT token of {get_jwt_identity()}")
            user = AUTH_SERVICE.get_user(user_id=get_jwt_identity())
            if not user:
                _log.error(f"Unable to refresh token of unknown user with id {get_jwt_identity()}")
            else:
                access_token = AUTH_SERVICE.create_jwt(user)
                set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError, PyJWTError):
        # Case where there is not a valid JWT. Just return the original response
        return response


@blueprint.route("/oauth2/login", methods=["GET"])
def oauth2_login():
    """
    Redirects the user to the OAuth2 server for login
    :return: 302 Redirect with the Oauth2 server URL in Location header
    """
    # oauth_client object is None (but defined) if OAuth2 login is not enabled
    oauth_client = current_app.oauth_client
    if oauth_client is None or current_app.config.get('APP_LOGIN_ENABLED', 'false') != 'true':
        return Response(json.dumps({'status': 'error', 'message': 'OAuth2 not enabled'}), status=409, mimetype='application/json')

    # Get the URL to the OAuth2 server
    provider_config = requests.get(current_app.config['APP_OAUTH_DISCOVERY_URL']).json()

    # Prepare client
    url, headers, body = oauth_client.prepare_authorization_request(
        authorization_url=provider_config['authorization_endpoint'],
        redirect_url=f"{current_app.config['APP_HOST_SCHEME']}://{current_app.config['APP_HOST']}/api/auth/oauth2/callback",
        scope=['openid', 'email', 'profile']
    )

    # Redirect the user to the OAuth2 server
    return Response(status=302, headers={'Location': url})


@blueprint.route("/oauth2/callback", methods=["GET"])
def oauth2_callback():
    """
    Callback endpoint for the OAuth2 server. Only the OAuth2 server should redirect the client to this endpoint.
    Calling this directly will result in an HTTP 400 error
    :return:
    """
    # oauth_client object is None (but defined) if OAuth2 login is not enabled
    oauth_client = current_app.oauth_client
    if oauth_client is None or current_app.config.get('APP_LOGIN_ENABLED', 'false') != 'true':
        return Response(json.dumps({'status': 'error', 'message': 'OAuth2 not enabled'}), status=409, mimetype='application/json')

    # Check if the OAuth2 server redirected the client with the correct (basic) parameters
    if not 'code' in request.args or not 'state' in request.args:
        return Response(json.dumps({'status': 'error', 'message': 'Invalid request'}), status=400, mimetype='application/json')

    # Get the URL to the OAuth2 server
    provider_config = requests.get(current_app.config['APP_OAUTH_DISCOVERY_URL']).json()

    try:
        # Prepare the request to retrieve the token from the OAuth2 server
        token_url, headers, body = oauth_client.prepare_token_request(
            provider_config['token_endpoint'],
            authorization_response=request.url,
            redirect_url=f"{current_app.config['APP_HOST_SCHEME']}://{current_app.config['APP_HOST']}/api/auth/oauth2/callback",
            code=request.args.get('code')
        )
        # Get the token
        token_response = requests.post(token_url,
                                       headers=headers,
                                       data=body,
                                       auth=(current_app.config['APP_OAUTH_CLIENT_ID'],
                                             current_app.config['APP_OAUTH_CLIENT_SECRET'])
                                       )
        # Parse the token
        oauth_client.parse_request_body_response(token_response.text)

        # Get the user info from the response
        userinfo_url, headers, body = oauth_client.add_token(provider_config['userinfo_endpoint'])
        userinfo_response = requests.get(userinfo_url, headers=headers, data=body)
        userinfo = userinfo_response.json()

    except OAuth2Error as e:
        # Regular errors, such as malformed or invalid codes and states
        return Response(json.dumps({'status': 'error', 'message': f'OAuth2 error: {e.description}'}), status=400, mimetype='application/json')
    except Exception as e:
        # Exceptional error, should not happen
        _log.error(f'OAuth2 error: unknown error {e}')
        return Response(json.dumps({'status': 'error', 'message': f'OAuth2 error: unknown error'}), status=500, mimetype='application/json')

    ### OAUTH2 procedure complete, now we can verify the user data

    try:
        # Check if user is already in the database
        # username is build of the first + lastname with whitespaces stripped
        username = (userinfo['name'] + " " + userinfo.get('family_name', '')).strip()
        user = AUTH_SERVICE.get_user(username=username)
        sso_id = userinfo['sub']
    except KeyError as e:
        # Missing userinfo field, should not happen though
        _log.error(f'OAuth2 error: missing userinfo field {e}')
        return Response(json.dumps({'status': 'error', 'message': f'OAuth2 error: The provider did not return required field {e}.'}), status=500, mimetype='application/json')

    ### Parsed the userinfo, now we can verify the user data with our own database

    if user is None:
        # Create user
        user = AUTH_SERVICE.create_user_oauth2(sso_id=sso_id, username=username, firstname=userinfo['given_name'], lastname=userinfo.get('family_name', ''))
    elif not user.uses_oauth2():
        return Response(json.dumps({'status': 'error', 'message': 'User already exists and does not use OAuth2. Please use the regular login instead'}), status=409, mimetype='application/json')
    else:
        # Check SSO ID, should be fine since username implies sso_id and both are unique
        if not user.credentials.authenticate({'sso_id': sso_id}):
            return Response(json.dumps({'status': 'error', 'message': 'OAuth2 ID mismatch'}), status=409, mimetype='application/json')

    ### Verification done, we can now generate the JWT token
    # Generate JWT token
    jwt = AUTH_SERVICE.create_jwt(user)
    AUTH_SERVICE.update_last_login(user)

    # Redirect user to the main page
    response = redirect(f"{current_app.config['APP_HOST_SCHEME']}://{current_app.config['APP_HOST']}/", code=302)

    # Attach JWT to the response as a cookie
    set_access_cookies(response, jwt, max_age=int(current_app.config.get('APP_JWT_TOKEN_EXPIRES', 3600))) # Set the JWT in the response as a cookie, valid for 1 hour
    return response


@blueprint.route("/password_reset", methods=["POST"])
def password_reset():
    """
    REST API endpoint for password reset
    Requires username and a new password as query parameters
    When succesful, the user should be redirected to the login page
    If not successful, returns an error message
    :return: Response
    """
    try:
        if current_app.config.get('APP_PASSWORD_RESET_ENABLED', 'true') != 'true':
            return Response(json.dumps({'status': 'error', 'message': "Password reset not enabled"}), status=409, mimetype='application/json')

        if 'username' not in request.args or 'password' not in request.args:
            return Response(json.dumps({'status': 'error', 'message': 'username and/or password not provided'}), status=400, mimetype='application/json')

        username = escape(request.args.get('username'))
        newPassword = escape(request.args.get('password'))
        firstname = escape(request.args.get('firstname'))
        lastname = escape(request.args.get('lastname'))

        # Check if the user exists
        user = AUTH_SERVICE.get_user(username=username)
        if user is None:
            return Response(json.dumps({'status': 'error', 'message': 'User not found'}), status=404, mimetype='application/json')

        if user.firstname != firstname or user.lastname != lastname:
            _log.warning(f'User {username} attempted to reset password with incorrect firstname and/or lastname')
            return Response(json.dumps({'status': 'error', 'message': 'User not found'}), status=404, mimetype='application/json')

        # Check if the user uses OAuth2
        if user.uses_oauth2():
            return Response(json.dumps({'status': 'error', 'message': 'User uses OAuth2. Authenticate using OAuth portal'}), status=409, mimetype='application/json')

        # Change the password
        user.credentials.change_password(newPassword)
        current_app.db.session.commit()

        return Response(json.dumps({'status': 'success', 'message': 'Password changed'}), status=200, mimetype='application/json')


    except (KeyError, ValueError) as e:
        return Response(json.dumps({'status': 'error', 'message': str(e)}), status=400, mimetype='application/json')


# Add the register endpoint to the Swagger docs
# God this is ugly
add_endpoint_to_swagger('/api/auth/register', 'post', ['auth'], 'Register a new user', 'Register a new user',
                        parameters=[{'name': 'username', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'The username of the new user'},
                         {'name': 'password', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'The password of the new user'},
                         {'name': 'firstname', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'The firstname of the new user'},
                         {'name': 'lastname', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'The lastname of the new user'}],
                        response_schemas={200: {'description': 'Success, returns the JWT token and user profile in JSON format', 'schema': {}},
                         409: {'description': 'Registration not enabled or username already taken', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}},
                         400: {'description': 'incorrect number of parameters', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}}})

# Add the login endpoint to the Swagger docs
add_endpoint_to_swagger('/api/auth/login', 'post', ['auth'], 'Login a user', 'Login a user',
                        parameters=[{'name': 'username', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'The username of the user'},
                         {'name': 'password', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'The password of the user'}],
                        response_schemas={200: {'description': 'Success, returns the JWT token and user profile in JSON format', 'schema': {}},
                         401: {'description': 'Username not found, invalid password or user uses OAuth2 login', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}},
                         409: {'description': 'Login not enabled', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}}})

# Add the logout endpoint to the Swagger docs
add_endpoint_to_swagger('/api/auth/logout', ['get', 'post'], ['auth'], 'Logout a user', 'Logout a user',
                        parameters=[],
                        response_schemas={200: {'description': 'Success, returns a message', 'schema': {'$ref': '#/components/schemas/SuccessSchema'}}})

# Add the OAuth2 login endpoint to the Swagger docs
add_endpoint_to_swagger('/api/auth/oauth2/login', 'get', ['auth'], 'Login with OAuth2.', 'Login with OAuth2.  This will start an OAuth2 login procedure and create a redirect URL to the OAuth2 provider login endpoint',
                        parameters=[],
                        response_schemas={302: {'description': 'Redirects the user to the OAuth2 server for login', 'schema': {}},
                                          409: {'description': 'OAuth2 not enabled', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}}})

# Add the OAuth2 callback endpoint to the Swagger docs
add_endpoint_to_swagger('/api/auth/oauth2/callback', 'get', ['auth'], 'OAuth2 callback.', 'OAuth2 callback. Should only be used by a redirect from the OAuth2 provider.',
                        parameters=[{'name': 'code', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'The OAuth2 code (recieved from the provider)'},
                                    {'name': 'state', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'The OAuth2 state (recieved from calling /api/auth/oauth2/login)'}],
                        response_schemas={302: {'description': 'Redirects the user to the main page (success)', 'schema': {}},
                                          400: {'description': 'Invalid request, OAuth2 error (specified)', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}},
                                          409: {'description': 'OAuth2 not enabled or OAuth2 ID mismatch (rare)', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}},
                                          500: {'description': 'OAuth2 error (unspecified or invalid response from provider)', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}}})

# Add the password reset endpoint to the Swagger docs
add_endpoint_to_swagger('/api/auth/password_reset', 'post', ['auth'], 'Reset the password of a user', 'Reset the password of a user',
                        parameters=[{'name': 'username', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'The username of the user'},
                                    {'name': 'password', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'The new password of the user'}],
                        response_schemas={200: {'description': 'Success, returns a message', 'schema': {'$ref': '#/components/schemas/SuccessSchema'}},
                                          400: {'description': 'username and/or password not provided', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}},
                                          404: {'description': 'User not found', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}},
                                          409: {'description': 'User uses OAuth2 or password reset is not enabled', 'schema': {'$ref': '#/components/schemas/ErrorSchema'}}})