import sqlalchemy.exc
from flask import request, current_app, Flask
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api
from flask import Blueprint as FlaskBlueprint


from src.model.blueprint import Blueprint
from src.resource import clean_dict_input, add_swagger, check_admin
from src.schema import ErrorSchema, SuccessSchema
from src.swagger_patches import Schema, summary


class BlueprintSchema(Schema):
    """
    The schema of the blueprint model when used in RESTful API
    """

    properties = {
        'id': {
            'type': 'integer',
            'format': 'int64'
        },
        'name': {
            'type': 'string'
        },
        'description': {
            'type': 'string'
        },
        'cost': {
            'type': 'integer',
            'format': 'int64'
        },
        'buildtime': {
            'type': 'integer',
            'format': 'int64'
        }
    }

    required = ['name', 'description', 'cost', 'buildtime']

    description = 'The blueprint model. A blueprint builds a building on an island. The player can build all buildings whose blueprints it has unlocked'

    def __init__(self, blueprint: Blueprint = None, **kwargs):
        if blueprint:
            super().__init__(id=blueprint.id, name=blueprint.name, description=blueprint.description,
                             cost=blueprint.cost,
                             buildtime=blueprint.buildtime, **kwargs)
        else:
            super().__init__(**kwargs)


class BlueprintResource(Resource):
    """
    A resource / api endpoint that allows for the retrieval and modification of blueprints
    Note: all endpoints except GET are restricted to admins
    """

    @swagger.tags('blueprint')
    @summary('Get a blueprint by id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The id of the blueprint to retrieve', required=True)
    @swagger.response(200, description='Success, returns the blueprint in JSON format', schema=BlueprintSchema)
    @swagger.response(404, description='Unknown blueprint id', schema=ErrorSchema)
    @swagger.response(400, description='Invalid or no blueprint id', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Get a blueprint by id
        The id is in the query parameter 'id'
        :return:
        """
        id = request.args.get('id', type=int)

        if id is None:
            return ErrorSchema('No blueprint id given'), 400

        blueprint = Blueprint.query.get(id)
        if blueprint is None:
            return ErrorSchema(f'Unknown blueprint id {id}'), 404
        else:
            return BlueprintSchema(blueprint), 200


    @swagger.tags('blueprint')
    @summary('Update a blueprint. All fields (except id) are updateable.')
    @swagger.expected(schema=BlueprintSchema, required=True)
    @swagger.response(200, description='Success, returns the updated blueprint in JSON format', schema=BlueprintSchema)
    @swagger.response(404, description='Unknown blueprint id', schema=ErrorSchema)
    @swagger.response(400, description='Invalid or no blueprint id', schema=ErrorSchema)
    @swagger.response(403, description='Caller is not an admin', schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update a blueprint by id
        :return:
        """
        # Check admin rights
        r = check_admin()
        if r:
            return r

        data = request.get_json()
        data = clean_dict_input(data)

        try:
            BlueprintSchema(**data, _check_requirements=False)
            id = int(data['id'])

            blueprint = Blueprint.query.get(id)
            if blueprint is None:
                return ErrorSchema(f'Unknown blueprint id {id}'), 404

            blueprint.update(data)
            current_app.db.session.commit()

            return BlueprintSchema(blueprint), 200

        except (ValueError, TypeError) as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('blueprint')
    @summary('Create a new blueprint')
    @swagger.expected(schema=BlueprintSchema, required=True)
    @swagger.response(200, description='Success, returns the created blueprint in JSON format', schema=BlueprintSchema)
    @swagger.response(400, description='Invalid blueprint data', schema=ErrorSchema)
    @swagger.response(403, description='Caller is not an admin', schema=ErrorSchema)
    @jwt_required()
    def post(self):
        """
        Create a new blueprint by id
        :return:
        """
        # Check admin rights
        r = check_admin()
        if r:
            return r

        data = request.get_json()
        data = clean_dict_input(data)

        try:
            BlueprintSchema(**data, _check_requirements=True)
            if 'id' in data:
                data.pop('id')

            blueprint = Blueprint(**data)
            current_app.db.session.add(blueprint)
            current_app.db.session.commit()
            return BlueprintSchema(blueprint), 200
        except (ValueError, TypeError) as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('blueprint')
    @summary('Delete a blueprint by id. Note that there may no longer be any buildings using this blueprint.')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The id of the blueprint to delete', required=True)
    @swagger.response(200, description='Success', schema=SuccessSchema)
    @swagger.response(404, description='Unknown blueprint id', schema=ErrorSchema)
    @swagger.response(400, description='Invalid or no blueprint id', schema=ErrorSchema)
    @swagger.response(409, description='Cannot delete blueprint as it is still in use by a building', schema=ErrorSchema)
    @swagger.response(403, description='Caller is not an admin', schema=ErrorSchema)
    @jwt_required()
    def delete(self):
        """
        Delete a blueprint by id
        Note: This won't work if the blueprint is still in use by a building
        :return:
        """
        # Check admin rights
        r = check_admin()
        if r:
            return r

        id = request.args.get('id', type=int)

        if id is None:
            return ErrorSchema('No blueprint id given'), 400

        blueprint = Blueprint.query.get(id)
        if blueprint is None:
            return ErrorSchema(f'Unknown blueprint id {id}'), 404
        else:
            try:
                current_app.db.session.delete(blueprint)
                current_app.db.session.commit()
                return SuccessSchema(), 200
            except sqlalchemy.exc.IntegrityError as e:
                if 'ForeignKeyViolation' in e.args[0]:
                    return ErrorSchema(f'Cannot delete blueprint {id} as it is still in use by a building'), 409
                else:
                    raise e


class BlueprintListResource(Resource):
    """
    An api/resource to retrieve all blueprints from
    """

    @swagger.tags('blueprint')
    @summary('Get all blueprints')
    @swagger.response(200, description='Success, returns a list of all blueprints in JSON format', schema=BlueprintSchema)
    @jwt_required()
    def get(self):
        """
        Get all blueprints
        :return:
        """
        blueprints = Blueprint.query.all()
        return [BlueprintSchema(blueprint) for blueprint in blueprints], 200


def attach_resource(app: Flask) -> None:
    """
    Attach the PlayerResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = FlaskBlueprint('api_blueprint', __name__)
    api = Api(blueprint)
    api.add_resource(BlueprintResource, '/api/blueprint')
    api.add_resource(BlueprintListResource, '/api/blueprint/list')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)