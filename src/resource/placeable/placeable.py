from flask import request, current_app, Blueprint, Flask
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.resource.task import TaskSchema
from src.resource import add_swagger, check_data_ownership
from src.schema import ErrorSchema, SuccessSchema
from src.resource.blueprint import BlueprintSchema
from src.model.placeable.placeable import Placeable
from src.swagger_patches import Schema, summary


class PlaceableSchema(Schema):
    """
    Schema for Placeable model
    This is only a base schema and should be subclassed for specific building types
    """
    _abstract_class = True

    type = 'object'
    properties = {
        'placeable_id': {
            'type': 'integer',
            'description': 'The unique id of the placeable'
        },
        'island_id': {
            'type': 'integer',
            'description': 'The unique identifier of the island that the placeable is build on'
        },
        'x': {
            'type': 'integer',
            'description': 'The x coordinate of the placeable, inside the grid'
        },
        'z': {
            'type': 'integer',
            'description': 'The z coordinate of the placeable, inside the grid'
        },
        'rotation': {
            'type': 'integer',
            'description': 'The rotation of the placeable. 0=North, 1=East, 2=South, 3=West'
        },
        'type': {
            'type': 'string',
            'description': 'The type of this placeable'
        },
        'blueprint': {
            'type': 'object',
            'items': BlueprintSchema,
        },
        'task': TaskSchema
    }

    required = ['island_id', 'x', 'z', 'rotation']

    title = 'Placeable'
    description = 'A model representing a building in the game. A placeable can only be moved with respect to the grid of the island'

    def __init__(self, placeable: Placeable = None, **kwargs):
        if placeable is not None:
            super().__init__(placeable_id=placeable.placeable_id,
                             island_id=placeable.island_id,
                             x=placeable.xpos,
                             z=placeable.zpos,
                             type=placeable.type,
                             blueprint=BlueprintSchema(placeable.blueprint),
                             rotation=placeable.rotation,
                             task=self._resolve_task_schema_for_type(placeable.task) if placeable.task is not None else None,
                             **kwargs)
        else:
            super().__init__(**kwargs)


    def _resolve_task_schema_for_type(self, task: any):
        """
        Resolve the task schema for the given task type
        :param task: THe task object to resolve the schema for
        :return: The schema for the given task type
        """
        if task.type == "building_upgrade_task":
            from src.resource.upgrade_task import BuildingUpgradeTaskSchema
            return BuildingUpgradeTaskSchema(task)
        elif task.type == "fuse_task":
            from src.resource.fuse_task import FuseTaskSchema
            return FuseTaskSchema(task)
        elif task.type == "task":
            return TaskSchema(task)
        else:
            raise ValueError(f'Cannot find Schema for unknown task type {task.type}')




class PlaceableResource(Resource):
    """
    A resource/api endpoint that allows for the retrieval and modification of placables
    More commonly the retrieval of placable sets on the grid of an island

    This class only has a DELETE functionality as the Placeable Model is a pure abstract class.
    Modifications and retrieval of placables are done through their respective subclass API endpoints.

    Listing of placables is done through the IslandResource
    """

    @swagger.tags('placeable')
    @summary('Delete a placeable by id')
    @swagger.parameter(_in='query', name='placeable_id', schema={'type': 'integer'}, required=True)
    @swagger.response(200, 'Success. Placeable has been deleted', schema=SuccessSchema)
    @swagger.response(404, 'Placeable not found', schema=ErrorSchema)
    @swagger.response(400, 'No placeable_id found', schema=ErrorSchema)
    @swagger.response(response_code=403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def delete(self):
        """
        Delete a placeable by id
        """
        id = request.args.get('placeable_id', type=int)
        if id is None:
            return ErrorSchema('No placeable_id found'), 400

        placeable = Placeable.query.get(id)
        if placeable is None:
            return ErrorSchema(f'Placeable {id} not found'), 404

        r = check_data_ownership(placeable.island_id)  # island_id == owner_id
        if r: return r

        current_app.db.session.delete(placeable)
        current_app.db.session.commit()
        return SuccessSchema(f'Placeable {id} has been deleted'), 200



def attach_resource(app: Flask) -> None:
    """
    Attach the PlaceableResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_placeable', __name__)
    api = Api(blueprint)
    api.add_resource(PlaceableResource, '/api/placeable')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)