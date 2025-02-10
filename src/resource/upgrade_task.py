from flask import request, current_app, Flask, Blueprint
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.model.upgrade_task import BuildingUpgradeTask
from src.resource import clean_dict_input, add_swagger, check_data_ownership
from src.resource.task import TaskSchema, TaskResource
from src.schema import IntArraySchema, ErrorSchema
from src.swagger_patches import summary


class BuildingUpgradeTaskSchema(TaskSchema):

    properties = {
        'to_level': {
            'type': 'integer',
            'description': 'The level the building should be upgraded to'
        },
        'used_crystals': {
            'type': 'integer',
            'description': 'The amount of crystals used for the upgrade'
        },
        'building_minions': IntArraySchema

    }

    required = TaskSchema.required + ['to_level', 'used_crystals']

    def __init__(self, task: BuildingUpgradeTask = None, **kwargs):
        if task is not None:
            super().__init__(task, to_level=task.to_level, used_crystals=task.used_crystals,
                             building_minions=[minion.entity_id for minion in task.building_minions], **kwargs)
        else:
            super().__init__(**kwargs)


class BuildingUpgradeTaskResource(Resource):

    @swagger.tags('task')
    @summary('Retrieve the building upgrade task with the given id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The task id to retrieve', required=True)
    @swagger.response(200, description='Success, returns the building upgrade task profile in JSON format', schema=BuildingUpgradeTaskSchema)
    @swagger.response(404, description='Unknown task id', schema=ErrorSchema)
    @jwt_required()  # for security
    def get(self):
        """
        Get the building upgrade task profile by id
        :return: The building upgrade task profile in JSON format
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema('No task id provided'), 400

        task = BuildingUpgradeTask.query.get(id)  # Get the task by PK (id)
        if task is None:
            return ErrorSchema('Unknown task id'), 404

        return BuildingUpgradeTaskSchema(task), 200


    @swagger.tags('task')
    @summary('Create a new building upgrade task object. Add builder_minions through the builder_minon endpoint.')
    @swagger.response(200, description='Building upgrade task object', schema=BuildingUpgradeTaskSchema)
    @swagger.response(400, description='Invalid task data (eg unknown building id)', schema=ErrorSchema)
    @swagger.response(response_code=409, description='Building is already being worked on', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (by island_id) (or admin)',
                      schema=ErrorSchema)
    @swagger.expected(BuildingUpgradeTaskSchema, required=True)
    @jwt_required()
    def post(self):
        """
        Create a new building upgrade task object
        :return: The building upgrade task object
        """
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            BuildingUpgradeTaskSchema(**data, _check_requirements=True)
            if 'to_level' not in data:
                raise ValueError('No to_level provided')
            if 'building_id' not in data:
                raise ValueError('No building_id provided')
            if 'used_crystals' not in data:
                raise ValueError('No used_crystals provided')
        except ValueError as e:
            return ErrorSchema(str(e)), 400

        r = TaskResource.parse_task_data(data, True)
        if r is not None:
            return r
        if 'id' in data:
            data.pop('id')

        task = BuildingUpgradeTask(**data)

        r = check_data_ownership(
            task.island_id)  # island_id == owner_id
        if r: return r

        current_app.db.session.add(task)
        current_app.db.session.commit()

        return BuildingUpgradeTaskSchema(task), 200


    @swagger.tags('task')
    @summary('Update the building upgrade task profile by id. Only the to_level, building_id and used_crystals can be updated. Update builder_minions through the builder_minon endpoint.')
    @swagger.response(200, description='Success', schema=BuildingUpgradeTaskSchema)
    @swagger.response(400, description='No task id provided', schema=ErrorSchema)
    @swagger.response(404, description='Unknown task id', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @swagger.expected(BuildingUpgradeTaskSchema, required=True)
    @jwt_required()
    def put(self):
        """
        Update the building upgrade task profile by id
        :return: The building upgrade task profile in JSON format
        """
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            BuildingUpgradeTaskSchema(**data, _check_requirements=False)
            id = int(data['id'])
        except (KeyError, ValueError) as e:
            return ErrorSchema(str(e)), 400


        task = BuildingUpgradeTask.query.get(id)
        if task is None:
            return ErrorSchema('Unknown task id'), 404

        r = TaskResource.parse_task_data(data, False)
        if r is not None:
            return r

        r = check_data_ownership(
            task.island_id)  # island_id == owner_id
        if r: return r

        task.update(data)
        current_app.db.session.commit()

        return BuildingUpgradeTaskSchema(task), 200


def attach_resource(app: Flask) -> None:
    """
    Attach the PlayerResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_building_upgrade_task', __name__)
    api = Api(blueprint)
    api.add_resource(BuildingUpgradeTaskResource, '/api/building_upgrade_task')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)
