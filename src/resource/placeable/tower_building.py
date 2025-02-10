from flask import request, Blueprint, current_app
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import swagger, Api

from src.model.placeable.tower_building import TowerBuilding
from src.resource import add_swagger, clean_dict_input, check_data_ownership
from src.resource.placeable.building import BuildingSchema, BuildingResource
from src.schema import ErrorSchema
from src.swagger_patches import summary


class TowerBuildingSchema(BuildingSchema):
    """
    The JSON schema for TowerBuilding representation
    Please refer to the Swagger documentation for the complete schema (due to inheritance)
    """

    properties = {
        'tower_type': {
            'type': 'string',
            'description': 'The type of the tower'
        }
    }

    required = ['tower_type'] + BuildingSchema.required

    title = 'TowerBuilding'
    description = ('A tower that shoots at enemy warior minions in multiplayer mode. '
                   'Note: removal of gems from a building is done through the gem endpoint by removing its association with this building')

    def __init__(self, tower_building: TowerBuilding = None, **kwargs):
        if tower_building is not None:
            super().__init__(tower_building, tower_type=tower_building.tower_type.value, **kwargs)
        else:
            super().__init__(**kwargs)


class TowerBuildingResource(BuildingResource):
    """
    A resource / api endpoint that allows for the retrieval and modification of new and existing towers.
    Delete it through the placeable endpoint
    """

    @swagger.tags('building')
    @summary("Retrieve a tower building by its placeable id")
    @swagger.parameter(_in='query', name='placeable_id', schema={'type': 'int'}, description='The tower building id to retrieve', required=True)
    @swagger.response(response_code=200, description="The tower building in JSON format", schema=TowerBuildingSchema)
    @swagger.response(response_code=404, description='Tower building not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve the tower with the given placeable id
        The id is given as a query parameter
        :return:
        """
        id = request.args.get('placeable_id', type=int)
        if id is None:
            return ErrorSchema('No placeable_id given'), 400

        tower = TowerBuilding.query.get(id)
        print(tower)
        if not tower:
            return ErrorSchema(f"Tower building {id} not found"), 404

        return TowerBuildingSchema(tower), 200


    @swagger.tags('building')
    @summary("Update the tower building object with the given id. Updateable fields are x,z,rotation, level & tower_type")
    @swagger.expected(schema=TowerBuildingSchema, required=True)
    @swagger.response(response_code=200, description="The tower building has been updated. The up-to-date object is returned", schema=TowerBuildingSchema)
    @swagger.response(response_code=404, description='Tower building not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update the tower building with the given placeable id
        :return:
        """
        # Get the JSON data from the request
        data = request.get_json()
        data = clean_dict_input(data)
        try:
            TowerBuildingSchema(**data, _check_requirements=False)
            id = int(data['placeable_id'])


            # Get the existing tower building
            tower = TowerBuilding.query.get(id)
            if not tower:
                return ErrorSchema(f'Tower building with id {id} not found'), 404

            r = check_data_ownership(tower.island_id)  # island_id == owner_id
            if r: return r

            # Update the tower building
            tower.update(data)

            current_app.db.session.commit()
            return TowerBuildingSchema(tower), 200

        except (ValueError, KeyError) as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('building')
    @summary("Create a new tower building")
    @swagger.expected(schema=TowerBuildingSchema, required=True)
    @swagger.response(response_code=200, description="The tower building has been created. The new object is returned", schema=TowerBuildingSchema)
    @swagger.response(response_code=400, description="Invalid input", schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def post(self):
        """
        Create a new tower building
        :return:
        """
        # Get the JSON input
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            if 'gems' in data:
                # Remove the gems from the building, they are managed by the gem endpoint
                data.pop('gems')
            if 'type' in data:
                # Remove the type field as it's not needed, it's always 'tower_building' since we're in the tower_building endpoint
                data.pop('type')
            if 'task' in data:
                # Remove the task field as it's managed by the task endpoint
                data.pop('task')
            if 'blueprint' in data:
                # Remove the blueprint field as it's always 'tower_building' since we're in the tower_building endpoint
                data.pop('blueprint')

            TowerBuildingSchema(**data, _check_requirements=True)  # Validate the input

            # Create the tower model & add it to the database
            if 'placeable_id' in data:
                data.pop('placeable_id') # let SQLAlchemy initialize the id

            tower = TowerBuilding(**data)

            r = check_data_ownership(tower.island_id)  # island_id == owner_id
            if r: return r

            current_app.db.session.add(tower)
            current_app.db.session.commit()
            return TowerBuildingSchema(tower), 200

        except ValueError as e:
            return ErrorSchema(str(e)), 400


def attach_resource(app) -> None:
    """
    Attach the TowerBuildingResource (API endpoint + Swagger docs) to the given Flask app
    :param app:  The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('tower_building_api', __name__)
    api = Api(blueprint)
    api.add_resource(TowerBuildingResource, '/api/placeable/tower_building')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)
