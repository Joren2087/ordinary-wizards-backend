from flask import request, Blueprint, Flask, current_app
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import swagger, Api

from src.resource import add_swagger, clean_dict_input, check_data_ownership
from src.model.placeable.wall_building import WallBuilding
from src.resource.placeable.building import BuildingResource, BuildingSchema
from src.schema import ErrorSchema
from src.swagger_patches import summary


class WallBuildingSchema(BuildingSchema):
    """
    The JSON schema for Fuse Table Building representation
    Please refer to the Swagger documentation for the complete schema (due to inheritance)
    """

    properties = {}
    required = []
    title = "Wall"

    description = "A schema representing the wall model. Note: removal of gems from a building is done through the gem endpoint by removing its association with this building"

    def __init__(self, wall_building: WallBuilding = None, **kwargs):
        if wall_building:
            super().__init__(building=wall_building, **kwargs)
        else:
            super().__init__(**kwargs)


class WallBuildingResource(BuildingResource):
    """
    A resource/api endpoint that allows the retrieval and modification of a Wall Building
    Delete it through the placeable endpoint
    """

    @swagger.tags('building')
    @summary("Retrieve the wall building object with the given id")
    @swagger.parameter(_in='query', name='placeable_id', schema={'type': 'int'}, description='The builder minion id to retrieve', required=True)
    @swagger.response(response_code=200, description="The wall building in JSON format",
                      schema=WallBuildingSchema)
    @swagger.response(response_code=404, description='Wall with given id not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve the fuse table building with the given placeable id
        The placeable id is in the query parameter 'placeable_id'
        :return:
        """
        id = request.args.get('placeable_id', type=int)
        if id is None:
            return ErrorSchema('No placeable_id given'), 400

        wall_building = WallBuilding.query.get(id)
        if not wall_building:
            return ErrorSchema(f'Wall with id {id} not found'), 404

        return WallBuildingSchema(wall_building), 200


    @swagger.tags('building')
    @summary("Update the wall building object with the given id. Updateable fields are x,z,rotation & level")
    @swagger.expected(schema=WallBuildingSchema, required=True)
    @swagger.response(response_code=200, description="The wall building has been updated. The up-to-date object is returned", schema=WallBuildingSchema)
    @swagger.response(response_code=404, description='Wall with given id not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update the fuse table building with the given placeable id
        :return:
        """
        # Get the JSON data from the request
        data = request.get_json()
        data = clean_dict_input(data)
        try:
            WallBuildingSchema(**data, _check_requirements=False)
            id = int(data['placeable_id'])


            # Get the existing fuse table building
            wall_building = WallBuilding.query.get(id)
            if not wall_building:
                return ErrorSchema(f'Wall with id {id} not found'), 404

            r = check_data_ownership(wall_building.island_id)  # island_id == owner_id
            if r: return r

            # Update the existing fuse table building
            wall_building.update(data)

            current_app.db.session.commit()
            return WallBuildingSchema(wall_building), 200
        except (ValueError, KeyError) as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('building')
    @summary("Create a new fuse table building")
    @swagger.expected(schema=WallBuildingSchema, required=True)
    @swagger.response(response_code=200, description="The fuse table building has been created. The new object is returned", schema=WallBuildingSchema)
    @swagger.response(response_code=400, description='Invalid input', schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def post(self):
        """
        Create a new fuse table building
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
                # Remove the type field as it's not needed, it's always 'wall_building' since we're in the wall_building endpoint
                data.pop('type')
            if 'task' in data:
                # Remove the task field as it's managed by the task endpoint
                data.pop('task')
            if 'blueprint' in data:
                data.pop('blueprint')

            WallBuildingSchema(**data, _check_requirements=True)

            # Create the tower model & add it to the database
            if 'placeable_id' in data:
                data.pop('placeable_id') # let SQLAlchemy initialize the id

            # Create the new fuse table building
            wall_building = WallBuilding(**data)

            r = check_data_ownership(wall_building.island_id)  # island_id == owner_id
            if r: return r

            current_app.db.session.add(wall_building)
            current_app.db.session.commit()
            return WallBuildingSchema(wall_building), 200

        except ValueError as e:
            return ErrorSchema(str(e)), 400



def attach_resource(app: Flask) -> None:
    """
    Attach the WallBuildingResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('wall_api', __name__)
    api = Api(blueprint)
    api.add_resource(WallBuildingResource, '/api/placeable/wall_building')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)