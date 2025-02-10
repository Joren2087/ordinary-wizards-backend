from flask import request, current_app, Flask, Blueprint
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import swagger, Api

from src.model.island import Island
from src.model.builder_minion import BuilderMinion
from src.resource import clean_dict_input, add_swagger, check_data_ownership
from src.resource.entity import EntitySchema, EntityResource
from src.schema import ErrorSchema, SuccessSchema
from src.swagger_patches import summary


class BuilderMinionSchema(EntitySchema):
    """
    The JSON schema for Builder Minion representation
    Please refer to the Swagger documentation for the complete schema (due to inheritance)
    """

    properties = {
        'builds_on': {
            'type': 'integer',
            'description': 'The building id that the builder minion is working on. The building should be upgrading when the builder minion is working on/assigned to it.'
        }
    }

    required = EntitySchema.required

    title = 'BuilderMinion'
    description = 'A model representing a builder minion in the game. A builder minion is a type of entity that can move on an island and can build buildings.'

    def __init__(self, builder_minion: BuilderMinion = None, **kwargs):
        if builder_minion is not None:
            super().__init__(builder_minion,
                             builds_on=builder_minion.builds_on.working_building.placeable_id if builder_minion.builds_on is not None else None,
                             **kwargs)
        else:
            super().__init__(**kwargs)


class BuilderMinionResource(EntityResource):
    """
    A resource/api endpoint that allows for the retrieval and modification of builder minions
    """

    @swagger.tags('entity')
    @summary('Retrieve the builder minion with the given id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The builder minion id to retrieve', required=True)
    @swagger.response(response_code=200, description='Successful retrieval', schema=BuilderMinionSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @swagger.response(response_code=404, description='Builder minion not found', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve the builder minion with the given id
        The id of the builder minion to retrieve is given as a query parameter
        :return: The builder minion in JSON format
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema('No id given'), 400

        builder_minion = BuilderMinion.query.get(id)
        if builder_minion is None:
            return ErrorSchema(f'Builder minion {id} not found'), 404

        return BuilderMinionSchema(builder_minion), 200


    @swagger.tags('entity')
    @summary('Create a new builder minion')
    @swagger.expected(schema=BuilderMinionSchema, required=True)
    @swagger.response(response_code=200, description='Builder minion created', schema=BuilderMinionSchema)
    @swagger.response(response_code=400, description='builds_on building id not found (when provided), island_id not found, or invalid input', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def post(self):
        """
        Create a new builder minion
        :return: The success message, or an error message
        """
        # Get the JSON input
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            BuilderMinionSchema(**data, _check_requirements=True)  # Validate the input
        except ValueError as e:
            return ErrorSchema(str(e)), 400

        # Create the BuilderMinion model & add it to the database
        if 'entity_id' in data:
            data.pop('entity_id') # let SQLAlchemy initialize the id

        # parse the integer building input to the actual task
        if 'builds_on' in data:
            from src.model.placeable.building import Building
            building = Building.query.get(data['builds_on'])
            if building is None:
                return ErrorSchema(f"Building with id {data['builds_on']} not found"), 400

            from src.model.upgrade_task import BuildingUpgradeTask
            if not isinstance(building.task, BuildingUpgradeTask):
                return ErrorSchema(f"Building with id {data['builds_on']} is not being upgraded"), 400

            data['builds_on'] = building.task # set the task

        if 'type' in data:
            # Remove the type field as it's not needed, it's always 'builder_minion' since we're in the builder_minion endpoint
            data.pop('type')


        builder_minion = BuilderMinion(**data)

        r = check_data_ownership(builder_minion.island_id)  # island_id == owner_id
        if r: return r

        island = Island.query.get(builder_minion.island_id)
        if island is None:
            return ErrorSchema(f"Island with id {builder_minion.island_id} not found"), 400


        current_app.db.session.add(builder_minion)
        current_app.db.session.commit()
        return BuilderMinionSchema(builder_minion), 200

    @swagger.tags('entity')
    @summary('Update an existing builder minion. Updateable fields are x,y,z, level & builds_on')
    @swagger.expected(schema=BuilderMinionSchema, required=True)
    @swagger.response(200, description='Builder minion successfully updated. The up-to-date object is returned', schema=BuilderMinionSchema)
    @swagger.response(404, description="Builder minion not found", schema=ErrorSchema)
    @swagger.response(400, description="Invalid input", schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update a builder minion by its id (from query)
        :return:
        """
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            BuilderMinionSchema(**data, _check_requirements=False)
            id = int(data['entity_id'])


            minion = BuilderMinion.query.get(id)
            if minion is None:
                return ErrorSchema(f"Builder minion with id {id} not found"), 404

            # parse the integer building input to the actual task
            if 'builds_on' in data:
                from src.model.placeable.building import Building
                building = Building.query.get(data['builds_on'])
                if building is None:
                    return ErrorSchema(f"Building with id {data['builds_on']} not found"), 400

                from src.model.upgrade_task import BuildingUpgradeTask
                if not isinstance(building.task, BuildingUpgradeTask):
                    return ErrorSchema(f"Building with id {data['builds_on']} is not being upgraded"), 400

                data['builds_on'] = building.task  # set the task

            if 'island_id' in data:
                island = Island.query.get(int(data['island_id']))
                if island is None:
                    return ErrorSchema(f"Island with id {data['island_id']} not found"), 400

            r = check_data_ownership(minion.island_id)  # island_id == owner_id
            if r: return r

            minion.update(data)

            current_app.db.session.commit()
            return BuilderMinionSchema(minion), 200
        except (ValueError, KeyError) as e:
            return ErrorSchema(str(e)), 400


def attach_resource(app: Flask) -> None:
    """
    Attach the BuilderMinionResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_builder_minion', __name__)
    api = Api(blueprint)
    api.add_resource(BuilderMinionResource, '/api/entity/builder_minion')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)