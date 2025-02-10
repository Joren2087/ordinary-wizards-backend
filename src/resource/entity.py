from flask import request, current_app, Flask, Blueprint
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.resource import add_swagger, check_data_ownership
from src.schema import SuccessSchema, ErrorSchema
from src.model.entity import Entity
from src.swagger_patches import Schema, summary


class EntitySchema(Schema):
    """
    Schema for the Entity model.
    This is only a base schema and should be subclassed for specific entity types.
    """
    _abstract_class = True

    type = 'object'
    properties = {
        'entity_id': {
            'type': 'integer',
            'description': 'The unique identifier of the entity'
        },
        'island_id': {
            'type': 'integer',
            'description': 'The unique identifier of the island that the entity is on'
        },
        'x': {
            'type': 'integer',
            'description': 'The x coordinate of the entity'
        },
        'y': {
            'type': 'integer',
            'description': 'The y coordinate of the entity'
        },
        'z': {
            'type': 'integer',
            'description': 'The z coordinate of the entity'
        },
        'type': {
            'type': 'string',
            'description': 'The type of the entity'
        },
        'level': {
            'type': 'integer',
            'description': 'The level of the entity'
        }
    }
    required = ['island_id', 'x', 'y', 'z']

    title = 'Entity'
    description = 'A model representing an entity in the game. An entity is a movable object that can moved without dependence on the grid of an island'

    def __init__(self, entity: Entity = None, **kwargs):
        if entity is not None:  # entity -> schema
            super().__init__(entity_id=entity.entity_id, x=entity.xpos,
                             y=entity.ypos, z=entity.zpos, type=entity.type,
                             island_id=entity.island_id, level=entity.level,
                             **kwargs)
        else:  # schema -> entity
            super().__init__(**kwargs)


class EntityResource(Resource):
    """
    A resource/api endpoint that allows for the retrieval and modification of entities
    More commonly the retrieval of entity sets, placable sets (buildings) and owner information.

    This class has only a delete functionality as the Entity Model is a pure abstract class.
    Modifications and retrieval of entites is done through their respective subclass API endpoints.

    Listing of entities is done through the IslandResource.
    """


    @swagger.tags('entity')
    @summary('Delete the entity with the given id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The entity id to delete', required=True)
    @swagger.response(200, description='Success, the entity was deleted', schema=SuccessSchema)
    @swagger.response(404, description='Unknown entity id', schema=ErrorSchema)
    @swagger.response(400, description='No entity id found', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def delete(self):
        """
        Delete the entity with the given id
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema('No entity id found'), 400

        entity = Entity.query.get(id)
        if entity is None:
            return ErrorSchema(f'Entity {id} not found'), 404

        r = check_data_ownership(entity.island_id)  # island_id == owner_id
        if r: return r

        current_app.db.session.delete(entity)
        current_app.db.session.commit()

        return SuccessSchema('Entity has been deleted'), 200


def attach_resource(app: Flask):
    """
    Attach the PlaceableResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_entity', __name__)
    api = Api(blueprint)
    api.add_resource(EntityResource, '/api/entity')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)
