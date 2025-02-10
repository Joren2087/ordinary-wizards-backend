from flask import request, current_app, Flask, Blueprint
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.resource import clean_dict_input, check_data_ownership, add_swagger
from src.model.fuse_task import FuseTask
from src.resource.task import TaskSchema, TaskResource
from src.schema import ErrorSchema
from src.swagger_patches import summary


class FuseTaskSchema(TaskSchema):

    properties = {
        'crystal_amount': {
            'type': 'integer',
            'description': 'The amount of crystals used for the fusion'
        }
    }

    required = TaskSchema.required + ['crystal_amount', 'building_id']

    def __init__(self, task: FuseTask = None, **kwargs):
        if task is not None:
            super().__init__(task, crystal_amount=task.crystal_amount, **kwargs)
        else:
            super().__init__(**kwargs)



class FuseTaskResource(Resource):
    """
    A resource/api endpoint that allows the retrieval and modification of a Fuse Task
    """

    @swagger.tags('task')
    @summary('Retrieve the fuse task with the given id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The task id to retrieve', required=True)
    @swagger.response(200, description='Success, returns the fuse task profile in JSON format', schema=FuseTaskSchema)
    @swagger.response(404, description='Unknown task id', schema=ErrorSchema)
    @swagger.response(400, description='No id given', schema=ErrorSchema)
    @jwt_required()  # for security
    def get(self):
        """
        Retrieve the fuse task with the given id
        The task id is in the query parameter 'task_id'
        :return:
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema('No task_id given'), 400

        task = FuseTask.query.get(id)
        if not task:
            return ErrorSchema(f'Fuse task with id {id} not found'), 404

        return FuseTaskSchema(task), 200


    @swagger.tags('task')
    @summary('Create a new fuse task object')
    @swagger.expected(schema=FuseTaskSchema, required=True)
    @swagger.response(200, description='Success, returns the created fuse task object', schema=FuseTaskSchema)
    @swagger.response(400, description='Invalid input', schema=ErrorSchema)
    @swagger.response(response_code=409, description='Building is already being worked on', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (by island_id) (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def post(self):
        """
        Create a new fuse task object
        :return: The created fuse task object
        """
        data = request.get_json()
        data = clean_dict_input(data)
        try:
            FuseTaskSchema(**data, _check_requirements=True)

            r = TaskResource.parse_task_data(data, True)
            if r is not None:
                return r

            if 'id' in data:
                data.pop('id')

            task = FuseTask(**data)

            if task.working_building.type != 'fuse_table_building':
                return ErrorSchema(f'Building with id {task.working_building.placeable_id} is not a fuse table'), 400


            r = check_data_ownership(task.island_id)  # island_id == owner_id
            if r:
                return r

            current_app.db.session.add(task)
            current_app.db.session.commit()

            return FuseTaskSchema(task), 200
        except ValueError as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('task')
    @summary('Update the fuse task object with the given id')
    @swagger.expected(schema=FuseTaskSchema, required=True)
    @swagger.response(200, description='Success, returns the updated fuse task object', schema=FuseTaskSchema)
    @swagger.response(404, description='Fuse task with given id not found', schema=ErrorSchema)
    @swagger.response(400, description='No id given', schema=ErrorSchema)
    @swagger.response(403, description='Unauthorized access to data object. Calling user is not owner of the data (or admin)', schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update the fuse task object with the given id
        :return: The updated fuse task object
        """
        data = request.get_json()
        data = clean_dict_input(data)
        try:
            FuseTaskSchema(**data, _check_requirements=False)
            id = int(data['id'])

            task = FuseTask.query.get(id)
            if not task:
                return ErrorSchema(f'Fuse task with id {id} not found'), 404

            r = TaskResource.parse_task_data(data, False)
            if r is not None:
                return r

            r = check_data_ownership(task.island_id)  # island_id == owner_id
            if r:
                return r

            task.update(data)
            current_app.db.session.commit()

            return FuseTaskSchema(task), 200
        except Exception as e:
            return ErrorSchema(str(e)), 400


def attach_resource(app: Flask) -> None:
    """
    Attach the PlayerResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_fuse_task', __name__)
    api = Api(blueprint)
    api.add_resource(FuseTaskResource, '/api/fuse_task')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)