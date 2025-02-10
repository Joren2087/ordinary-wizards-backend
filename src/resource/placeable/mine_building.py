import datetime

from flask import request, Flask, Blueprint, current_app
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import swagger, Api, Resource

from src.model.placeable.mine_building import MineBuilding
from src.resource import add_swagger, clean_dict_input, check_data_ownership
from src.resource.gems import GemSchema
from src.resource.placeable.building import BuildingSchema
from src.schema import ErrorSchema
from src.swagger_patches import summary


class MineBuildingSchema(BuildingSchema):
    """
    The JSON schema for Mine Building representation
    Please refer to the Swagger documentation for the complete schema (due to inheritance)
    """

    properties = {
        'mine_type': {
            'type': 'string',
            'description': 'The type of the mine'
        },
        'last_collected': {
            'type': 'string',
            'format': 'date-time',
            'description': 'The datetime when the mine was last emptied'
        }
    }

    required = ['mine_type'] + BuildingSchema.required

    title = 'MineBuilding'
    description = ('A mine that mines a certain type of resource and keeps it until it is emptied by the player. '
                   'Note: removal of gems from a building (or here, the collected gem) is done through the gem endpoint by removing its association with this building')

    def __init__(self, mine: MineBuilding = None, **kwargs):
        if mine is not None:
            super().__init__(mine,
                             mine_type=mine.mine_type.value,
                             last_collected=str(mine.last_collected).replace(' ', 'T'),
                             **kwargs)
        else:
            super().__init__(**kwargs)


class MineBuildingResource(Resource):
    """
    A resource / api endpoint that allows for the retrieval and modification of
    new and existing mines.
    Delete it through the placeable endpoint
    """

    @swagger.tags('building')
    @summary("Retrieve a mine building by its placeable id")
    @swagger.parameter(_in='query', name='placeable_id', schema={'type': 'int'}, description='The mine building id to retrieve', required=True)
    @swagger.response(response_code=200, description="The altar building in JSON format", schema=MineBuildingSchema)
    @swagger.response(response_code=404, description='Builder minion not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve the mine with the given placeable id
        The id is given as a query parameter
        :return:
        """
        id = request.args.get('placeable_id', type=int)
        if id is None:
            return ErrorSchema('No placeable_id given'), 400

        mine = MineBuilding.query.get(id)
        if not mine:
            return ErrorSchema(f"Mine building {id} not found"), 404

        return MineBuildingSchema(mine), 200


    @swagger.tags('building')
    @summary("Update the mine building object with the given id. Updateable fields are x,z,rotation, level, mine_type & mined_amount")
    @swagger.expected(schema=MineBuildingSchema, required=True)
    @swagger.response(response_code=200, description="The mine building has been updated. The up-to-date object is returned", schema=MineBuildingSchema)
    @swagger.response(response_code=404, description='Mine building not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update the mine building with the given placeable id
        :return:
        """
        # Get the JSON data from the request
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            MineBuildingSchema(**data, _check_requirements=False)
            id = int(data['placeable_id'])

            # Get the existing mine building
            mine = MineBuilding.query.get(id)
            if not mine:
                return ErrorSchema(f'Mine building with id {id} not found'), 404

            # Convert the datetime strings to datetime objects
            if 'last_collected' in data:
                data['last_collected'] = data['last_collected'].replace('T', ' ')
                data["last_collected"] = data["last_collected"].split(".")[0]
                data['last_collected'] = datetime.datetime.strptime(data['last_collected'], '%Y-%m-%d %H:%M:%S')

            r = check_data_ownership(mine.island_id)  # island_id == owner_id
            if r: return r

            # Update the mine building
            mine.update(data)

            current_app.db.session.commit()
            return MineBuildingSchema(mine), 200
        except (ValueError, KeyError) as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('building')
    @summary("Create a new mine building")
    @swagger.expected(schema=MineBuildingSchema, required=True)
    @swagger.response(response_code=200, description="The mine building has been created. The new object is returned", schema=MineBuildingSchema)
    @swagger.response(response_code=400, description="Invalid input", schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def post(self):
        """
        Create a new mine building
        :return: The success message, or an error message
        """
        # Get the JSON input
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            if 'gems' in data:
                # Remove the gems from the building, they are managed by the gem endpoint
                data.pop('gems')
            if 'type' in data:
                # Remove the type field as it's not needed, it's always 'mine_building' since we're in the mine_building endpoint
                data.pop('type')
            if 'task' in data:
                # Remove the task field as it's managed by the task endpoint
                data.pop('task')
            if 'blueprint' in data:
                # Remove the blueprint field as it's always 'mine_building' since we're in the mine_building endpoint
                data.pop('blueprint')

            MineBuildingSchema(**data, _check_requirements=True)  # Validate the input


            # Create the MineBuilding model & add it to the database
            if 'placeable_id' in data:
                data.pop('placeable_id') # let SQLAlchemy initialize the id

            mine = MineBuilding(**data)

            r = check_data_ownership(mine.island_id)  # island_id == owner_id
            if r: return r

            current_app.db.session.add(mine)
            current_app.db.session.commit()
            return MineBuildingSchema(mine), 200

        except (ValueError, KeyError) as e:
            return ErrorSchema(str(e)), 400




def attach_resource(app: Flask) -> None:
    """
    Attach the MineBuildingResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_mine_building', __name__)
    api = Api(blueprint)
    api.add_resource(MineBuildingResource, '/api/placeable/mine_building')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)
