import logging
import os
from json import JSONEncoder
from logging.handlers import RotatingFileHandler

import werkzeug.exceptions
from concurrent_log_handler import ConcurrentRotatingFileHandler
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_migrate import check as check_db_schema
from flask_migrate import upgrade as upgrade_db_schema
from flask_restful_swagger_3 import get_swagger_blueprint
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2 import WebApplicationClient
from sqlalchemy.orm import DeclarativeBase

"""
This is the main entry point for the application.

Direclty invocating this file will start the Flask debug server.
When using a production server, use the WSGI script (wsgi.py) with a production WSGI server (e.g. gunicorn) to start the app.
"""


class Base(DeclarativeBase):
    pass


class JSONClassEncoder:
    """
    JSON Encoder that calls to_json() on objects
    """

    def __init__(self, *args, **kwargs):
        pass

    def default(self, o):
        if hasattr(o, '_to_json'):
            return JSONEncoder().default(o._to_json())
        else:
            return JSONEncoder().default(o)

    def encode(self, o):
        if hasattr(o, '_to_json'):
            return JSONEncoder().encode(o._to_json())
        else:
            return JSONEncoder().encode(o)


# Load environment variables
assert load_dotenv(".env"), "unable to load .env file"
from os import environ
from src.logger_formatter import CustomFormatter

# Configure the logger

handlers = []
logfile = environ.get('APP_LOG_FILE', None)
if logfile:
    fh = ConcurrentRotatingFileHandler(logfile, maxBytes=100000, backupCount=1)  # Set delay to prevent WinError 32
    handlers.append(fh)

streamHandler = logging.StreamHandler()
streamHandler.setFormatter(CustomFormatter())
handlers.append(streamHandler)

if environ.get('APP_DEBUG', "false") == "true":
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                        handlers=handlers)
    logging.debug("Debug mode enabled")
else:
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=handlers
                        )

db: SQLAlchemy = SQLAlchemy(model_class=Base)
app: Flask = Flask(environ.get('APP_NAME'))

@app.errorhandler(Exception)
def log_exception(error):
    # Log the exception
    msg = f"Exception occurred: {error}"
    status = 500
    if isinstance(error, werkzeug.exceptions.HTTPException) and error.code < 500:
        msg = error.__str__()
        status = error.code

    if request:
        if 'api' in request.url:
            msg = jsonify({'status': 'error', 'message': msg})

        if status >= 500:
            app.logger.exception(f"Exception occurred: {error} in {request.url}")
        else:
            app.logger.debug(f"Exception occurred: {error} in {request.url} - probably user error")
        return msg, status
    else:
        app.logger.exception(f"Exception occurred: {error}")

    return 'Internal Server Error', 500

def setup_jwt(app: Flask):
    """
    Setup the JWT manager for the given Flask app
    Uses the APP_JWT_SECRET_KEY environment variable to load the secret key

    Generate a secret key with:
    <pre>
    import secrets
    with open('jwtRS256.key', 'wb') as f:
         f.write(secrets.token_bytes(256))
    </pre>

    :param app:
    :return:
    """
    logging.debug("Setting up JWT")
    # Configure JWT
    app.config['JWT_ALGORITHM'] = 'HS256'  # HMAC SHA-256

    # Load the secret key from file
    with open(app.config.get('APP_JWT_SECRET_KEY', 'jwtRS256.key'), 'rb') as f:  # The secret key to sign our JWTs with
        app.config['JWT_SECRET_KEY'] = f.read()

    app.config['JWT_TOKEN_LOCATION'] = ['cookies']  # only look for tokens in the cookies
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(app.config.get('APP_JWT_TOKEN_EXPIRES', 3600))  # token expires, defaults to 1h
    app.config['JWT_SESSION_COOKIE'] = True  # Use cookies for session, removed once browser closes
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Disable CSRF protection (for now)
    app.config['JWT_COOKIE_SECURE'] = app.config.get('APP_HOST_SCHEME',
                                                     'https') == 'https'  # Serve cookies only over HTTPS, default to do so

    # Create the JWT manager
    app.jwt = JWTManager(app)

    # Add a custom error handler for JWT errors
    _jwt_log = logging.getLogger("_jwt")

    @app.jwt.invalid_token_loader
    @app.jwt.token_verification_failed_loader
    def custom_invalid_token_loader(callback):
        _jwt_log.debug(f"Invalid token (check format?): {callback}")
        return jsonify({'status': 'error', 'message': 'Unauthorized', 'type': 'jwt_invalid_token'}), 401

    @app.jwt.unauthorized_loader
    def custom_unauthorized_loader(callback):
        _jwt_log.debug(f"Unauthorized (no cookie?): {callback}")
        return jsonify({'status': 'error', 'message': 'Unauthorized', 'type': 'jwt_no_cookie'}), 401

    @app.jwt.expired_token_loader
    def custom_expired_token_loader(jwt_header, jwt_data):
        _jwt_log.debug(f"Expired token (log back in): {jwt_header}, {jwt_data}")
        # return redirect("/landing", code=401)
        return jsonify(
            {'status': 'error', 'message': 'Token has expired (log back in)', 'type': 'jwt_token_expired'}), 401


def setup(app: Flask):
    """
    Set up the Flask app with the given configuration from environment variables (in .env or system)
    Also initializes the database (SQLAlchemy), JWT manager, imports & registers the routes, setup the Swagger API,
    setup SocketIO and generate the documentation
    :param app: The flask app
    :return: None
    """
    logging.debug("Setting up app")

    # Create the Flask app
    # app: Flask = Flask()

    # Key differs in production, this is good enough for dev purposes
    app.secret_key = environ.get('APP_SECRET_KEY') or '*^*(*&)(*)(*afafafaSDD47j\3yX R~X@H!jmM]Lwf/,?KT'

    # Load config variables from environment variables
    for var in environ:
        if var.startswith('APP_'):
            app.config[var] = environ.get(var)

    # Check if requires config variables are set
    assert app.config.get('APP_POSTGRES_USER') is not None, "APP_POSTGRES_USER not set"
    assert app.config.get('APP_POSTGRES_DATABASE') is not None, "APP_POSTGRES_DATABASE not set"

    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        (f"postgresql://{app.config['APP_POSTGRES_USER']}:{app.config['APP_POSTGRES_PASSWORD']}"
         f"@{app.config['APP_POSTGRES_HOST']}:{app.config['APP_POSTGRES_PORT']}"
         f"/{app.config['APP_POSTGRES_DATABASE']}")

    # Needed to have Flask to propagate exceptions in order to have the JWT exception handlers to work properly
    # See SCRUM-45
    app.config['PROPAGATE_EXCEPTIONS'] = True

    # Configre JWT
    setup_jwt(app)

    # Initialize the db with our Flask instance
    db.init_app(app)
    app.db = db

    # Configure OAuth2 client
    if app.config.get("APP_DEBUG", "false") == "true":
        # Allow insecure transport in debug mode
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Initialize the OAuth2 client, this client will be used to authenticate users with the OAuth2 (Google) server
    app.oauth_client = None
    if app.config.get('APP_OAUTH_ENABLED', 'false') == 'true':
        app.oauth_client = WebApplicationClient(app.config['APP_OAUTH_CLIENT_ID'])

    # Lock the app context
    with app.app_context():
        # import routes INSIDE the app context
        import src.routes
        app.register_blueprint(src.routes.public_routes.blueprint)
        app.register_blueprint(src.routes.api_auth.blueprint, url_prefix='/api/auth')

        # Register custom JSON Encoder to call to_json() on objects
        # This is so that Flask can jsonify our SQLAlchemy models
        app.config['RESTFUL_JSON'] = {'cls': JSONClassEncoder}

        # Create all API endpoints
        from src.resource import attach_resources
        attach_resources(app)

        # Create the tables in the db, AFTER entities are imported
        # Create the DB migration manager
        app.migrate = Migrate(app=app, db=app.db, directory='migrations')

        if app.config.get('APP_AUTOMIGRATE', "true") == "true":
            # Automatically migrate the database
            upgrade_db_schema()

        if app.config.get('APP_DISABLE_SCHEMA_VALIDATION', "false") != "true":
            # Check if the database schema is up to date
            # We allow inconsistencies in debug mode, but not in production
            check_db_schema()

        # Setup SWAGGER API documentation (only when enabled)
        if app.config.get('APP_SWAGGER_ENABLED', "false") == 'true':
            from src.resource import openapi_dict
            logging.info("Setting up Swagger API documentation")
            app.config['SWAGGER_BLUEPRINT_URL_PREFIX'] = '/api/docs'
            swagger_url = app.config.get('APP_SWAGGER_URL', '/api/docs')
            api_url = app.config.get('APP_SWAGGER_API_URL', '/static/swagger.json')
            resource = get_swagger_blueprint(openapi_dict, add_api_spec_resource=True,
                                             swagger_url=swagger_url, swagger_prefix_url=api_url,
                                             title=app.config['APP_NAME'])
            app.register_blueprint(resource, url_prefix=swagger_url)

        app.socketio = SocketIO(cors_allowed_origins='*')
        app.socketio.init_app(app)
        from src.socketio import attach_namespaces
        attach_namespaces(app)

        # Annoy user when data ownership is not strictly enforced
        if app.config.get('CHECK_DATA_OWNERSHIP', 'true') != 'true':
            logging.warning("Data ownership checks will not block requests (they will log a warning).")

        # Generate documentation
        from documentation import generate_pdoc
        generate_pdoc(generate=app.config.get('APP_GENERATE_DOCS', 'false') == 'true')  # to generate documentation set parameter to true: generate_pdoc(True)
    return app, app.socketio


# RUN DEV SERVER

app, socketio = setup(app)


if __name__ == "__main__":
    # Finally, run the app
    # don't put this in the setup() as the WSGI server uses that function as well
    logging.info("Booting Flask Debug server")
    app_bind = app.config['APP_BIND']
    debug = app.config.get('APP_DEBUG', 'False').lower() == 'true'
    socketio.run(app, debug=debug, allow_unsafe_werkzeug=True)
