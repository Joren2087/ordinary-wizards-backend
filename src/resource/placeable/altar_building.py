from flask import request, Flask, Blueprint, current_app
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import swagger, Api, Resource

from src.model.placeable.altar_building import AltarBuilding
from src.resource import add_swagger, clean_dict_input, check_data_ownership
from src.resource.placeable.building import BuildingSchema, BuildingResource
from src.schema import ErrorSchema, SuccessSchema
from src.swagger_patches import summary


class AltarBuildingSchema(BuildingSchema):
    """
    The JSON schema for Altar Building representation
    Please refer to the Swagger documentation for the complete schema (due to inheritance)
    """

    properties = {}
    required = []

    title = "Altar Building"
    description = ("A model representing the Altar Building in the game. Note: Only one altar building can exist on an island. "
                   "Note: removal of gems from a building is done through the gem endpoint by removing its association with this building")

    def __init__(self, altar_building: AltarBuilding = None, **kwargs):
        if altar_building:
            super().__init__(altar_building, **kwargs)
        else:
            super().__init__(**kwargs)

class AltarBuildingResource(Resource):
    """
    A resource/api endpoint that allows the retrieval and modification of an Altar Building
    This would be most commonly be used to move its position or change it's level.
    No new altar can be made as only one may exist on an island. Therefore, no POST endpoint exits
    Delete it through the placeable endpoint
    """

    @swagger.tags('building')
    @summary("Retrieve the altar building object with the given id")
    @swagger.parameter(_in='query', name='placeable_id', schema={'type': 'int'}, description='The builder minion id to retrieve', required=True)
    @swagger.response(response_code=200, description="The altar building in JSON format", schema=AltarBuildingSchema)
    @swagger.response(response_code=404, description='Altar table with given id not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve the altar building with the given placeable id
        The id of the placeable to retrieve is given as query parameter
        :return: The altar building in JSON format
        """
        id = request.args.get("placeable_id", type=int)
        if id is None:
            return ErrorSchema('No id given'), 400

        altar_building = AltarBuilding.query.get(id)
        if altar_building is None:
            return ErrorSchema(f"Altar building {id} not found"), 404

        return AltarBuildingSchema(altar_building), 200


    @swagger.tags('building')
    @summary("Update the altar building object with the given id. Updateable fields are x,z,rotation & level")
    @swagger.expected(schema=AltarBuildingSchema, required=True)
    @swagger.response(response_code=200, description="Success schema", schema=SuccessSchema)
    @swagger.response(response_code=404, description='Altar table with given id not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update the altar building with the given placeable id
        The id of the placeable to update is given in the JSON body
        :return:
        """
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            AltarBuildingSchema(**data, _check_requirements=False)
            id = int(data["placeable_id"])
        except (ValueError, KeyError) as e:
            return ErrorSchema(str(e)), 400

        altar_building = AltarBuilding.query.get(id)
        if altar_building is None:
            return ErrorSchema(f"Altar building {id} not found"), 404

        r = check_data_ownership(altar_building.island_id)  # island_id == owner_id
        if r: return r

        altar_building.update(data)

        current_app.db.session.commit()
        return SuccessSchema(f"Altar building {id} successfully updated"), 200



def attach_resource(app: Flask) -> None:
    """
    Attach the BuilderMinionResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_altar_building', __name__)
    api = Api(blueprint)
    api.add_resource(AltarBuildingResource, '/api/placeable/altar_building')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)
