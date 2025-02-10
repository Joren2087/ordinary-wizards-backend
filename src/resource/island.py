from flask import request, Flask, Blueprint
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.resource.placeable.placeable import PlaceableSchema
from src.resource import add_swagger
from src.resource.entity import EntitySchema
from src.schema import ErrorSchema
from src.swagger_patches import Schema
from src.model.island import Island
from src.swagger_patches import summary


class IslandSchema(Schema):
    """
    Schema for the Island model
    """
    type = 'object'
    properties = {
        'owner_id': {
            'type': 'integer',
            'description': 'The unique identifier of the island. This equals to the owner\'s user_profile_id'
        },
        'entities': {
            'type': 'array',
            'items': EntitySchema,
            'description': 'The entities on the island. This includes buildings, builder minions and other entities. The illustrated schema might be incomplete, refer to the type-sepcific schema for more information'
        },
        'placeables': {
            'type': 'array',
            'items': PlaceableSchema,
            'description': 'The placeables on the island. This includes buildings, builder minions and other entities. The illustrated schema might be incomplete, refer to the type-sepcific schema for more information'
        }
    }
    required = []

    title = 'Island'
    description = 'A model representing an island in the game. Owned by a player with the same id'

    def __init__(self, island: Island = None, **kwargs):
        if island is not None: # island -> schema
            super().__init__(owner_id=island.owner_id,
                             entities=[self._resolve_entity_schema_for_type(entity) for entity in island.entities],
                             placeables=[self._resolve_placeable_schema_for_type(placeable) for placeable in island.placeables])
        else: # schema -> island
            super().__init__(**kwargs)

    def _resolve_entity_schema_for_type(self, entity: any):
        """
        Resolve the schema for the given entity type
        :param entity: The entity object to resolve the schema for
        :return: The schema for the given entity type
        :raises ValueError: If the entity type is unknown to this function
        """
        if entity.type == 'builder_minion':
            from src.resource.builder_minion import BuilderMinionSchema
            return BuilderMinionSchema(entity)
        elif entity.type == 'player':
            from src.resource.player import PlayerEntitySchema
            return PlayerEntitySchema(entity)

        raise ValueError(f'Cannot find Schema for unknown entity type {entity.type}')

    def _resolve_placeable_schema_for_type(self, placeable: any):
        """
        Resolve the schema for the given placeable type
        :param placeable: The placeable object to resolve the schema for
        :return: THe schema for the given placeable type
        :raises ValueError: If the placeable type is unknown to this function
        """
        if placeable.type == 'fuse_table_building':
            from src.resource.placeable.fuse_table_building import FuseTableBuildingSchema
            return FuseTableBuildingSchema(placeable)
        elif placeable.type == 'altar_building':
            from src.resource.placeable.altar_building import AltarBuildingSchema
            return AltarBuildingSchema(placeable)
        elif placeable.type == 'mine_building':
            from src.resource.placeable.mine_building import MineBuildingSchema
            return MineBuildingSchema(placeable)
        elif placeable.type == 'warrior_hut_building':
            from src.resource.placeable.warrior_hut_building import WarriorHutBuildingSchema
            return WarriorHutBuildingSchema(placeable)
        elif placeable.type == 'tower_building':
            from src.resource.placeable.tower_building import TowerBuildingSchema
            return TowerBuildingSchema(placeable)
        elif placeable.type == 'prop':
            from src.resource.placeable.prop import PropSchema
            return PropSchema(placeable)
        elif placeable.type == 'wall_building':
            from src.resource.placeable.wall_building import WallBuildingSchema
            return WallBuildingSchema(placeable)

        raise ValueError(f'Cannot find Schema for unknown placeable type {placeable.type}')


class IslandResource(Resource):
    """
    A resource/api endpoint that allows for the retrieval and modification of islands
    More commonly the retrieval of entity sets, placable sets (buildings) and owner information.
    """

    @swagger.tags('island')
    @summary('Retrieve the island with the given id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The island id to retrieve', required=True)
    @swagger.response(response_code=200, description='Successful retrieval', schema=IslandSchema)
    @swagger.response(response_code=404, description='Island not found', schema=ErrorSchema)
    @swagger.response(response_code=400, description='No id given', schema=ErrorSchema)
    @jwt_required()
    def get(self):
        """
        Retrieve the island with the given id in query parameter
        :return: The island in JSON format
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema('No id given'), 400

        island = Island.query.get(id)
        if island is None:
            return ErrorSchema(f'Island {id} not found'), 404


        return IslandSchema(island), 200


def attach_resource(app: Flask) -> None:
    """
    Attach the IslandResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_island', __name__)
    api = Api(blueprint)
    api.add_resource(IslandResource, '/api/island')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)