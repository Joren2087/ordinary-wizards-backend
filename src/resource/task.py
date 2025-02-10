import datetime

from flask import request, current_app, Flask, Blueprint
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.model.task import Task
from src.resource import clean_dict_input, add_swagger, check_data_ownership
from src.schema import ErrorSchema, SuccessSchema
from src.swagger_patches import Schema, summary


class TaskSchema(Schema):
    """
    Schema for the Task object
    """

    properties = {
        'id': {
            'type': 'integer',
            'format': 'int64',
            'description': 'The unique identifier of the task'
        },
        'island_id': {
            'type': 'integer',
            'format': 'int64',
            'description': 'The island id that the task is associated with'
        },
        'starttime': {
            'type': 'string',
            'format': 'date-time',
            'description': 'The time when the task started'
        },
        'endtime': {
            'type': 'string',
            'format': 'date-time',
            'description': 'The time when the task should end'
        },
        'type': {
            'type': 'string',
            'description': 'The type of the task'
        },
        'building_id': {
            'type': 'integer',
            'description': 'The building id that the task is associated with. Usually means the building that the task is working on (generating gems in a mine etc, or upgrading).'
        }
    }

    required = ['island_id', 'endtime']
    type = 'object'
    description = 'A Task object that represents an idle task. A task can be anything, but it is usually an idle task such as a mine that is mining minerals or a building that is in construction or in upgrade.'

    def __init__(self, task: Task = None, **kwargs):
        if task is not None:
            super().__init__(id=task.id, starttime=str(task.starttime).replace(' ', 'T'),
                             endtime=str(task.endtime).replace(' ', 'T'),
                             type=task.type, island_id=task.island_id,
                             building_id=task.working_building.placeable_id if task.working_building is not None else None,
                             **kwargs)
        else:
            super().__init__(**kwargs)


class TaskResource(Resource):
    """
    Resource for the task object
    """

    @staticmethod
    def parse_task_data(data: dict, new_task: bool):
        if 'endtime' in data:
            data['endtime'] = data['endtime'].replace('T', ' ')
            data['endtime'] = datetime.datetime.strptime(data['endtime'], '%Y-%m-%d %H:%M:%S')
            if new_task and data['endtime'] < datetime.datetime.now():
                return ErrorSchema(message='Endtime is in the past'), 400

        if 'starttime' in data:
            data['starttime'] = data['starttime'].replace('T', ' ')
            data['starttime'] = datetime.datetime.strptime(data['starttime'], '%Y-%m-%d %H:%M:%S')

        if 'endtime' in data and 'starttime' in data and data['endtime'] <  data['starttime']:
            return ErrorSchema(message='Endtime is before starttime'), 400

        if 'building_id' in data:
            building_id = int(data.pop('building_id'))
            from src.model.placeable.placeable import Placeable
            building = current_app.db.session.query(Placeable).get(building_id)
            if building is None:
                return ErrorSchema(message='Placeable id not found'), 400
            if building.island_id != data['island_id']:
                return ErrorSchema(message='Placeable does not belong to this island_id'), 400
            if new_task and building.task is not None and not building.task.is_over():
                return ErrorSchema(message='Placeable is already being worked on'), 409

            data['working_building'] = building

    @swagger.tags('task')
    @summary('Retrieve a task object by id')
    @swagger.parameter(_in='query', name='id', description="The id of the task to retrieve", schema={'type': 'integer', 'format': 'int64'}, required=True)
    @swagger.response(response_code=200, description='Task object', schema=TaskSchema)
    @swagger.response(response_code=404, description='Task not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No task id provided', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve a task object by id
        :return: The task object
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema(message='No task id provided'), 400

        task = Task.query.get(id)
        if task is None:
            return ErrorSchema(message='Task not found'), 404

        return TaskSchema(task), 200


    @swagger.tags('task')
    @summary('Create a new task object')
    @swagger.response(response_code=200, description='Task object', schema=TaskSchema)
    @swagger.response(response_code=400, description='Unknown building id (when provided) or invalid task data', schema=ErrorSchema)
    @swagger.response(response_code=409, description='Placeable is already being worked on', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (by island_id) (or admin)',
                      schema=ErrorSchema)
    @swagger.expected(TaskSchema, required=True)
    @jwt_required()
    def post(self):
        """
        Create a new task object
        :return: The task object
        """
        data = request.get_json()
        data = clean_dict_input(data)
        try:
            TaskSchema(**data, _check_requirements=True)

            r = TaskResource.parse_task_data(data, True)
            if r is not None:
                return r

            task = Task(**data)

            r = check_data_ownership(
                task.island_id)  # island_id == owner_id
            if r: return r

            current_app.db.session.add(task)
            current_app.db.session.commit()

            return TaskSchema(task), 200
        except ValueError as e:
            return ErrorSchema(message=str(e)), 400


    @swagger.tags('task')
    @summary('Update a task object by id. Only endtime & working_building are modifiable. Use DELETE to cancel a task')
    @swagger.response(response_code=200, description='Task object', schema=TaskSchema)
    @swagger.response(response_code=400, description='Unknown building id (when provided) or invalid task data', schema=ErrorSchema)
    @swagger.response(response_code=404, description='Task not found', schema=ErrorSchema)
    @swagger.response(response_code=409, description='Placeable is already being worked on', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @swagger.expected(TaskSchema, required=True)
    @jwt_required()
    def put(self):
        """
        Update a task object by id
        :return:
        """
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            TaskSchema(**data, _check_requirements=False)

            task = Task.query.get(int(data['id']))
            if task is None:
                return ErrorSchema(message='Task id not found'), 404

            r = TaskResource.parse_task_data(data, False)
            if r is not None:
                return r

            r = check_data_ownership(
                task.island_id)  # island_id == owner_id
            if r: return r

            task.update(data)
            current_app.db.session.commit()

            return TaskSchema(task), 200
        except ValueError as e:
            return ErrorSchema(message=str(e)), 400


    @swagger.tags('task')
    @summary('Delete a task object by id (or cancel it)')
    @swagger.parameter(_in='query', name='id', description="The id of the task to delete", schema={'type': 'integer', 'format': 'int64'}, required=True)
    @swagger.response(response_code=200, description='Task object', schema=SuccessSchema)
    @swagger.response(response_code=404, description='Task not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No task id provided', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def delete(self):
        """
        Delete a task object by id
        :return:
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema(message='No task id provided'), 400

        task = Task.query.get(id)
        if task is None:
            return ErrorSchema(message='Task not found'), 404

        r = check_data_ownership(
            task.island_id)  # island_id == owner_id
        if r: return r

        current_app.db.session.delete(task)
        current_app.db.session.commit()

        return SuccessSchema(f"Task with id {id} sucessfully deleted"), 200



class TaskListResource(Resource):
    """
    Resource for the list of tasks
    """

    @swagger.tags('task')
    @summary('Retrieve a list of tasks')
    @swagger.parameter(_in='query', name='island_id', description="The island id to retrieve the tasks from", schema={'type': 'integer', 'format': 'int64'}, required=True)
    @swagger.parameter(_in='query', name='is_over', description="When set, filter on is_over state", schema={'type': 'bool'}, required=False)
    @swagger.response(response_code=200, description='List of all tasks of an island in a JSON array. Empty if island id is invalid or no tasks are associated with this island', schema=TaskSchema)
    @swagger.response(response_code=400, description='No island id provided', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve a list of tasks
        :return: The list of tasks
        """
        island_id = request.args.get('island_id', type=int)
        if island_id is None:
            return ErrorSchema(message='No island id provided'), 400

        query = Task.query.filter_by(island_id=island_id)

        if 'is_over' in request.args:
            is_over: bool = request.args.get('is_over').lower() == "true"
            query = query.filter(Task.endtime < current_app.db.func.now() if is_over else Task.endtime >= current_app.db.func.now())

        tasks = query.all()
        return [TaskSchema(task) for task in tasks], 200


def attach_resource(app: Flask) -> None:
    """
    Attach the PlayerResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_task', __name__)
    api = Api(blueprint)
    api.add_resource(TaskResource, '/api/task')
    api.add_resource(TaskListResource, '/api/task/list')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)
