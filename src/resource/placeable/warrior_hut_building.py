from flask import request, Flask, Blueprint, current_app
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import swagger, Api

from src.model.placeable.warrior_hut_building import WarriorHutBuilding
from src.resource import add_swagger, clean_dict_input, check_data_ownership
from src.resource.placeable.building import BuildingSchema, BuildingResource
from src.schema import ErrorSchema
from src.swagger_patches import summary


class WarriorHutBuildingSchema(BuildingSchema):
    """
    The JSON schema for Warrior Hut Building representation
    Please refer to the Swagger documentation for the complete schema (due to inheritance)
    """

    properties = {}

    required = []

    title = "Warrior hut"
    description = "A schema representing the Warrior hut model. Note: removal of gems from a building is done through the gem endpoint by removing its association with this building"

    def __init__(self, warrior_hut_building: WarriorHutBuilding = None, **kwargs):
        if warrior_hut_building:
            super().__init__(warrior_hut_building, **kwargs)
        else:
            super().__init__(**kwargs)


class WarriorHutBuildingResource(BuildingResource):
    """
    A resource/api endpoint that allows the retrieval and modification of a Warrior Hut Buildings
    Delete it through the placeable endpoint
    """

    @swagger.tags('building')
    @summary("Retrieve the warrior hut building object with the given id")
    @swagger.parameter(_in='query', name='placeable_id', schema={'type': 'int'}, description='The warrior hut id to retrieve', required=True)
    @swagger.response(response_code=200, description="The warrior hut building in JSON format", schema=WarriorHutBuildingSchema)
    @swagger.response(response_code=404, description='Warrior hut with given id not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve the warrior hut building with the given placeable id
        The id is given as a query parameter
        :return:
        """
        id = request.args.get('placeable_id', type=int)
        if id is None:
            return ErrorSchema('No placeable_id given'), 400

        warrior_hut_building = WarriorHutBuilding.query.get(id)
        if not warrior_hut_building:
            return ErrorSchema(f'Warrior hut with id {id} not found'), 404

        return WarriorHutBuildingSchema(warrior_hut_building), 200


    @swagger.tags('building')
    @summary("Update the warrior hut building object with the given id. Updateable fields are x,z,rotation & level")
    @swagger.expected(schema=WarriorHutBuildingSchema, required=True)
    @swagger.response(response_code=200, description="The updated warrior hut building in JSON format", schema=WarriorHutBuildingSchema)
    @swagger.response(response_code=404, description='Warrior hut with given id not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update the warrior hut building with the given placeable id
        The id is given as a query parameter
        :return:
        """
        # Get the JSON data from the request
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            WarriorHutBuildingSchema(**data, _check_requirements=False)
            id = int(data['placeable_id'])

            # Get the existing warrior hut building
            warrior_hut_building = WarriorHutBuilding.query.get(id)
            if not warrior_hut_building:
                return ErrorSchema(f'Warrior hut with id {id} not found'), 404

            r = check_data_ownership(warrior_hut_building.island_id)  # island_id == owner_id
            if r: return r

            # Update the warrior hut building
            warrior_hut_building.update(data)

            current_app.db.session.commit()
            return WarriorHutBuildingSchema(warrior_hut_building), 200
        except (KeyError, ValueError) as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('building')
    @summary("Create a new warrior hut building")
    @swagger.expected(schema=WarriorHutBuildingSchema, required=True)
    @swagger.response(response_code=200, description="The created warrior hut building in JSON format", schema=WarriorHutBuildingSchema)
    @swagger.response(response_code=400, description='Invalid input', schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def post(self):
        """
        Create a new warrior hut building
        :return:
        """
        # Get the JSON data from the request
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            if 'gems' in data:
                # Remove the gems from the building, they are managed by the gem endpoint
                data.pop('gems')
            if 'type' in data:
                # Remove the type field as it's not needed, it's always 'warrior_hut_building' since we're in the warrior_hut_building endpoint
                data.pop('type')
            if 'task' in data:
                # Remove the task field as it's managed by the task endpoint
                data.pop('task')
            if 'blueprint' in data:
                # Remove the blueprint field as it's always 'warrior_hut_building' since we're in the warrior_hut_building endpoint
                data.pop('blueprint')

            WarriorHutBuildingSchema(**data, _check_requirements=True)

            # Create the tower model & add it to the database
            if 'placeable_id' in data:
                data.pop('placeable_id')  # let SQLAlchemy initialize the id

            warrior_hut_building = WarriorHutBuilding(**data)

            r = check_data_ownership(warrior_hut_building.island_id)  # island_id == owner_id
            if r: return r

            current_app.db.session.add(warrior_hut_building)
            current_app.db.session.commit()

            return WarriorHutBuildingSchema(warrior_hut_building), 200
        except (KeyError, ValueError) as e:
            return ErrorSchema(str(e)), 400



def attach_resource(app: Flask) -> None:
    """
    Attach the MineBuildingResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('warrior_hut_api', __name__)
    api = Api(blueprint)
    api.add_resource(WarriorHutBuildingResource, '/api/placeable/warrior_hut')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)
