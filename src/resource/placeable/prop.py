from flask import request, current_app, Flask, Blueprint
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.model.blueprint import Blueprint as BlueprintModel
from src.model.placeable.prop import Prop
from src.resource import clean_dict_input, add_swagger, check_data_ownership
from src.resource.placeable.placeable import PlaceableSchema
from src.schema import ErrorSchema
from src.swagger_patches import summary


class PropSchema(PlaceableSchema):
    properties = {
        'prop_type': {
            'type': 'string',
            'description': 'The type of prop'
        }
    }

    required = PlaceableSchema.required + ['prop_type']

    title = 'Prop'
    description = 'A model representing a prop in the game.'

    def __init__(self, prop: Prop = None, **kwargs):
        if prop is not None:
            super().__init__(prop, prop_type=prop.prop_type, **kwargs)
        else:
            super().__init__(**kwargs)


class PropResource(Resource):
    """
    A resource that allows for the retrieval and modification of props
    Delete it through the placeable endpoint
    """

    @swagger.tags('placeable')
    @summary('Get a prop by id')
    @swagger.parameter(_in='query', name='placeable_id', schema={'type': 'integer'}, required=True)
    @swagger.response(200, 'Success', schema=PropSchema)
    @swagger.response(404, 'Prop not found', schema=ErrorSchema)
    @swagger.response(400, 'No placeable_id found', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Get a prop by id
        """
        id = request.args.get('placeable_id', type=int)
        if id is None:
            return ErrorSchema('No placeable_id found'), 400

        prop = Prop.query.get(id)
        if prop is None:
            return ErrorSchema('Prop not found'), 404

        return PropSchema(prop), 200

    @swagger.tags('placeable')
    @summary('Update a prop by id. Note that you cannot change the blueprint afterwards. Updateable fields are x,z,rotation & prop_type ')
    @swagger.expected(schema=PropSchema, required=True)
    @swagger.response(200, 'Success', schema=PropSchema)
    @swagger.response(404, 'Prop not found', schema=ErrorSchema)
    @swagger.response(400, 'Invalid input', schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update a prop by id
        """
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            PropSchema(**data, _check_requirements=False)  # Validate the input

            prop = Prop.query.get(int(data['placeable_id']))
            if prop is None:
                return ErrorSchema("Prop id not found"), 404

            r = check_data_ownership(prop.island_id)  # island_id == owner_id
            if r: return r

            prop.update(data)

            current_app.db.session.commit()

            return PropSchema(prop), 200

        except (ValueError, KeyError) as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('placeable')
    @summary('Create a new prop')
    @swagger.expected(schema=PropSchema, required=True)
    @swagger.response(200, 'Success', schema=PropSchema)
    @swagger.response(400, 'Invalid input', schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def post(self):
        """
        Create a new prop
        """
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            # This is not required by the schema as the other buildings set these depending on the used subclass/endpoint
            # However, we need to ensure it's set here
            if 'blueprint_id' in data:
                blueprint_id = data.pop('blueprint_id')
                # Check if the blueprint exists
                if BlueprintModel.query.get(blueprint_id) is None:
                    raise ValueError(f'Blueprint with id {blueprint_id} not found')
            else:
                # We will try to resolve the blueprint from the prop_type
                if 'prop_type' in data:
                    prop_type = data['prop_type']
                    blueprint = BlueprintModel.query.filter_by(name=prop_type).first()
                    if blueprint is None:
                        raise ValueError(
                            f'Blueprint with name {prop_type} not found. Specify a blueprint_id instead.')
                    else:
                        blueprint_id = blueprint.id

            PropSchema(**data, _check_requirements=True)  # Validate the input
            if 'placeable_id' in data:
                data.pop('placeable_id')
            if 'type' in data:
                # Remove the type field as it's not needed, it's always 'prop' since we're in the prop endpoint
                data.pop('type')
            if 'island_id' in data:
                # check if island_id exists
                from src.model.island import Island
                if Island.query.get(data['island_id']) is None:
                    raise ValueError(f'Island with id {data["island_id"]} not found')

            if 'task' in data:
                # Remove the task field as it's not handled here
                data.pop('task')


            prop = Prop(**data, blueprint_id=blueprint_id)

            r = check_data_ownership(prop.island_id)  # island_id == owner_id
            if r: return r

            current_app.db.session.add(prop)
            current_app.db.session.commit()

            return PropSchema(prop), 200

        except (ValueError, KeyError) as e:
            return ErrorSchema(str(e)), 400


def attach_resource(app: Flask) -> None:
    """
    Attach the MineBuildingResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('prop_api', __name__)
    api = Api(blueprint)
    api.add_resource(PropResource, '/api/placeable/prop')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)
