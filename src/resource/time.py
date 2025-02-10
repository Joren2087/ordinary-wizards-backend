import datetime

from flask import Flask, Blueprint
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.resource import add_swagger
from src.swagger_patches import Schema, summary


class TimeSchema(Schema):

    properties = {
        'time': {
            'type': 'string',
            'format': 'date-time',
            'description': 'The current server time in ISO format'
        }
    }

    required = ['time']
    type = 'object'

    def __init__(self, time: datetime.datetime = None, **kwargs):
        if time is not None:
            super().__init__(time = str(time).replace(' ', 'T'), **kwargs)
        else:
            super().__init__(**kwargs)


class TimeResource(Resource):

    @swagger.tags(['time'])
    @summary('Get the current server time. This is used so that the frontend has a trusted source of time')
    @swagger.response(response_code=200, description='The current server time', schema=TimeSchema)
    @jwt_required()
    def get(self):
        """
        Get the current server time
        """
        return TimeSchema(time = datetime.datetime.now()), 200



def attach_resource(app: Flask) -> None:
    """
    Attach the TimeResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_time', __name__)
    api = Api(blueprint)
    api.add_resource(TimeResource, '/api/time')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)