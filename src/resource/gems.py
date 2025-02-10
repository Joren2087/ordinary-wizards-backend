from flask import Flask, Blueprint, request, current_app
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.model.gems import GemAttributeAssociation, Gem, GemAttribute
from src.resource import add_swagger, clean_dict_input, check_data_ownership
from src.schema import ErrorSchema, ArraySchema
from src.swagger_patches import Schema, summary


class GemAttributeAssociationSchema(Schema):
    """
    The association schema between a gem and a gem attribute with a multiplier as relationship attribute
    It is usually, if not exclusively, used with the GemSchema
    """
    properties = {
        'gem_attribute_id': {
            'type': 'integer',
            'format': 'int64'
        },
        'gem_attribute_type': {
            'type': 'string'
        },
        'multiplier': {
            'type': 'number',
            'format': 'float'
        }
    }

    required = ['gem_attribute_id', 'gem_attribute_type', 'multiplier']

    description = 'The association between a gem and a gem attribute with a multiplier as relationship attribute'

    def __init__(self, assoc: GemAttributeAssociation = None, **kwargs):
        if assoc:
            super().__init__(gem_attribute_id=assoc.gem_attribute_id, gem_attribute_type=assoc.attribute.type, multiplier=assoc.multiplier, **kwargs)
        else:
            super().__init__(**kwargs)

class GemAttributeSchema(Schema):
    """
    The schema for the gem attribute model. Get a list of all gem attributes
    """

    properties = {
        'id': {
            'type': 'integer',
            'format': 'int64'
        },
        'type': {
            'type': 'string'
        }
    }

    required = []

    description = 'A gem attribute object'

    def __init__(self, gem_attribute: GemAttribute = None, **kwargs):
        if gem_attribute:
            super().__init__(id=gem_attribute.id, type=gem_attribute.type, **kwargs)
        else:
            super().__init__(**kwargs)



class GemSchema(Schema):
    """
    The schema for the gem model. Get a list of a single gem with all its associated attributes and their multipliers
    """

    properties = {
        'id': {
            'type': 'integer',
            'format': 'int64'
        },
        'type': {
            'type': 'string'
        },
        'attributes': {
            'type': 'array',
            'items': GemAttributeAssociationSchema
        },
        'building_id': {
            'type': 'integer',
            'format': 'int64',
            'nullable': True,
        },
        'player_id': {
            'type': 'integer',
            'format': 'int64',
            'nullable': True,
        },
        'staked': {
            'type': 'boolean',
            'description': 'Whether the gem is used as a stake in a multiplayer match or not. Staked gems are "reserved" and cannot be used for boosting buildings or mines',
        }
    }

    required = ['type', 'attributes']

    description = 'A gem object with its attributes and their multipliers'

    def __init__(self, gem: Gem = None, **kwargs):
        if gem:
            super().__init__(id=gem.id,
                             type=gem.type.value,
                             attributes=[GemAttributeAssociationSchema(assoc) for assoc in gem.attributes_association],
                             building_id=gem.building_id,
                             player_id=gem.player_id,
                             staked=gem.staked,
                             **kwargs)
        else:
            super().__init__(**kwargs)


class GemResource(Resource):
    """
    A resource/api endpoint that allows for the retrieval and modification of gems
    """

    @swagger.tags('gems')
    @swagger.response(200, description='Success, returns the gem and its attributes in JSON format', schema=GemSchema)
    @swagger.response(404, description='Unknown gem id', schema=ErrorSchema)
    @swagger.response(400, description='Invalid or no gem id', schema=ErrorSchema)
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The gem id to retrieve', required=True)
    @summary('Get the gem by id')
    @jwt_required()
    def get(self):
        """
        Get a gem with its attributes and multipliers by id
        :return: The gem and its attributes in JSON format
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema('No gem id given'), 400

        gem = Gem.query.get(id)
        if gem is None:
            return ErrorSchema(f'Unknown gem id {id}'), 404
        else:
            return GemSchema(gem), 200


    @swagger.tags('gems')
    @summary('Update a gem by id. All fields (except ids) are updatable. Including attributes and their multipliers.'
             'A null building_id means the gem is in (island) storage, player_id must always be set')
    @swagger.expected(schema=GemSchema, required=True)
    @swagger.response(200, description='Success, returns the updated gem in JSON format', schema=GemSchema)
    @swagger.response(404, description='Unknown gem id', schema=ErrorSchema)
    @swagger.response(400, description='Invalid or no gem id', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def put(self):
        """
        Update a gem by id
        :return: The updated gem in JSON format
        """
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            GemSchema(**data, _check_requirements=False)
            id = int(data['id'])

            gem = Gem.query.get(id)
            if gem is None:
                return ErrorSchema(f'Unknown gem id {id}'), 404

            r = check_data_ownership(gem.player_id) # Check the owner id
            if r: return r

            gem.update(data)
            current_app.db.session.commit()

            return GemSchema(gem), 200
        except (ValueError, TypeError) as e:
            return ErrorSchema(str(e)), 400



    @swagger.tags('gems')
    @summary('Create a new gem')
    @swagger.expected(schema=GemSchema, required=True)
    @swagger.response(200, description='Success, returns the created gem in JSON format', schema=GemSchema)
    @swagger.response(400, description='Invalid input', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def post(self):
        """
        Create a new gem
        :return: The created gem in JSON format
        """
        # Get the JSON input
        data = request.get_json()
        data = clean_dict_input(data)

        try:
            # Check the input
            GemSchema(**data, _check_requirements=True)

            if 'id' in data:
                data.pop('id') # let SQLAlchemy initialize the id

            # So this is a bit tricky
            # We need to give a gem id to the attributes, but no (valid) id exists at this stage as
            # we need the db to give us a new gem id
            # Thus, we first create the gem without the attributes, then add the attributes with the gem id
            gem_attributes = []
            if 'attributes' in data:
                gem_attributes = data.pop('attributes')

            building_id = None
            if 'building_id' in data:
                building_id = data.pop('building_id')

            gem = Gem(**data)

            r = check_data_ownership(gem.player_id) # Check the owner id
            if r: return r

            current_app.db.session.add(gem)
            current_app.db.session.commit() # This is necessary to get the gem id

            # We reuse the update method to add the attributes
            gem.update({'attributes': gem_attributes, 'building_id': building_id})

            current_app.db.session.commit()

            return GemSchema(gem), 200
        except (KeyError, ValueError) as e:
            return ErrorSchema(str(e)), 400


    @swagger.tags('gems')
    @summary('Delete a gem by id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The gem id to delete', required=True)
    @swagger.response(200, description='Success', schema=ErrorSchema)
    @swagger.response(404, description='Gem not found', schema=ErrorSchema)
    @swagger.response(400, description='Invalid input', schema=ErrorSchema)
    @swagger.response(response_code=403,
                      description='Unauthorized access to data object. Calling user is not owner of the data (or admin)',
                      schema=ErrorSchema)
    @jwt_required()
    def delete(self):
        """
        Delete a gem by id
        :return: Success or error message
        """
        id = request.args.get('id', type=int)
        if id is None:
            return ErrorSchema('No gem id given'), 400

        gem = Gem.query.get(id)
        if gem is None:
            return ErrorSchema(f'Gem {id} not found'), 404

        r = check_data_ownership(gem.player_id)  # Check the owner id
        if r: return r

        current_app.db.session.delete(gem)
        current_app.db.session.commit()
        return ErrorSchema(f'Gem {id} deleted'), 200



class GemAttributeListResource(Resource):
    """
    A resource/api endpoint that allows for the listing of all gem attributes
    """

    @swagger.tags('gems')
    @summary('Get a list of all gem attributes')
    @swagger.reorder_list_with(schema=GemAttributeSchema, response_code=200, description='Success, returns a list of all gem attributes in JSON format')
    @jwt_required()
    def get(self):
        """
        Get a list of all gem attributes
        :return: A list of all gem attributes in JSON format
        """
        return [GemAttributeSchema(assoc) for assoc in GemAttribute.query.all()], 200


def attach_resource(app: Flask) -> None:
    """
    Attach the PlayerResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_gems', __name__)
    api = Api(blueprint)
    api.add_resource(GemResource, '/api/gem')
    api.add_resource(GemAttributeListResource, '/api/gem/attributes/list')
    app.register_blueprint(blueprint, url_prefix='/') # Relative to api.add_resource path
    add_swagger(api)

