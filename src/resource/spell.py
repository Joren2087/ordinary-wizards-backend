from flask import Flask, Blueprint, request, current_app
from flask_jwt_extended import jwt_required
from flask_restful_swagger_3 import Resource, swagger, Api

from src.schema import ErrorSchema, SuccessSchema
from src.model.spell import Spell
from src.resource import add_swagger, clean_dict_input, check_admin
from src.swagger_patches import Schema, summary


class SpellSchema(Schema):
    """
    The schema for the spell response
    """
    type = 'object'
    properties = {
        'id': {
            'type': 'integer'
        },
        'name': {
            'type': 'string'
        }
    }
    required = ['name']

    def __init__(self, spell: Spell = None, **kwargs):
        if spell is not None:
            super().__init__(id=spell.id, name=spell.name)
        else:
            super().__init__(**kwargs)

class SpellResource(Resource):
    """
    A Spell resource is a resource/api endpoint that allows for the retrieval and modification of spell profiles
    Note: all endpoints except GET are restricted to admins
    """

    @swagger.tags('spell')
    @summary('Retrieve the spell with the given id')
    @swagger.parameter(_in='query', name='id', schema={'type': 'int'}, description='The spell id to retrieve',
                       required=True)
    @swagger.response(200, description='Success, returns the spell profile in JSON format', schema=SpellSchema)
    @swagger.response(404, description='Unknown spell id', schema=ErrorSchema)
    @jwt_required()  # for security
    def get(self):
        """
        Get the spell profile by id
        :return: The spell profile in JSON format
        """
        if 'id' not in request.args:
            return ErrorSchema('No spell id provided'), 400

        id = int(request.args.get('id'))
        spell = Spell.query.get(id)  # Get the spell by PK (id)
        if spell is None:
            return ErrorSchema('Unknown spell id'), 404
        else:
            return SpellSchema(spell), 200


    @swagger.tags('spell')
    @summary('Create a new spell profile')
    @swagger.response(200, description='Success', schema=SpellSchema)
    @swagger.response(400, description='Invalid input', schema=ErrorSchema)
    @swagger.response(403, description='Caller is not an admin', schema=ErrorSchema)
    @swagger.expected(SpellSchema, required=True) # The expected input is a spell profile in JSON format, as defined by the SpellSchema class
    @jwt_required() # for security
    def post(self):
        """
        Create a new spell profile
        :return: The spell profile in JSON format
        """
        # Check admin rights
        r = check_admin()
        if r:
            return r


        # Get the JSON input
        data = request.get_json()
        data = clean_dict_input(data)
        try:
            SpellSchema(**data, _check_requirements=True)  # Validate the input
        except ValueError as e:
            return ErrorSchema(str(e)), 400

        # Create the spell model & add it to the database
        spell = Spell(**data)
        current_app.db.session.add(spell)
        current_app.db.session.commit()
        return SpellSchema(spell), 200

    @swagger.tags('spell')
    @summary('Update the spell profile by id. Only the name of a spell is modifiable')
    @swagger.response(200, description='Success', schema=SpellSchema)
    @swagger.response(404, description='Unknown spell id', schema=ErrorSchema)
    @swagger.response(400, description='Invalid or no spell id', schema=ErrorSchema)
    @swagger.response(403, description='Caller is not an admin', schema=ErrorSchema)
    @swagger.expected(SpellSchema, required=True)  # The expected input is a spell profile in JSON format, as defined by the SpellSchema class
    @jwt_required()  # for security
    def put(self):
        """
        Update the spell profile by id
        :return: The spell profile in JSON format
        """
        # Check admin rights
        r = check_admin()
        if r:
            return r

        # Get the JSON input
        data = request.get_json()
        data = clean_dict_input(data)
        try:
            SpellSchema(**data, _check_requirements=False)  # Validate the input
            id = int(data['id'])
        except (ValueError, KeyError) as e:
            return ErrorSchema(str(e)), 400

        # Get the existing spell profile
        spell = Spell.query.get(id)
        if spell is None:
            return ErrorSchema(f"Spell {id} not found"), 404
        spell.update(data)
        current_app.db.session.commit()
        return SpellSchema(spell), 200


    @swagger.tags('spell')
    @summary('Delete the spell profile by id. Note: this will remove all references to this spell in the database.')
    @swagger.response(200, description='Success', schema=SuccessSchema)
    @swagger.response(404, description='Unknown spell id', schema=ErrorSchema)
    @swagger.response(400, description='Invalid or no spell id', schema=ErrorSchema)
    @swagger.response(403, description='Caller is not an admin', schema=ErrorSchema)
    @jwt_required()  # for security
    def delete(self):
        """
        Delete the spell profile by id
        Note: this will remove all references to this spell in the database.
        :return: Success message
        """
        # Check admin rights
        r = check_admin()
        if r:
            return r

        if 'id' not in request.args:
            return ErrorSchema('No spell id provided'), 400

        id = int(request.args.get('id'))
        spell = Spell.query.get(id)
        if spell is None:
            return ErrorSchema('Unknown spell id'), 404
        else:
            # This should complete successfully, due to the CASCADE DELETE rule added to the constraint
            # in migration 4589aa4f65e1
            current_app.db.session.delete(spell)
            current_app.db.session.commit()
            return SuccessSchema(f"Spell with id {id} succesfully deleted"), 200


class SpellListResource(Resource):
    """
    A SpellList resource is a resource/api endpoint that allows for the retrieval of all spell profiles
    """

    @swagger.tags('spell')
    @summary('Get all spell profiles')
    @swagger.response(200, description='Success, returns all spell profiles in JSON array with SpellSchema objects in it', schema=SpellSchema)
    @jwt_required()  # for security
    def get(self):
        """
        Get all spell profiles
        :return: All spell profiles in JSON format
        """
        spells = Spell.query.all()
        return [SpellSchema(spell) for spell in spells], 200


def attach_resource(app: Flask) -> None:
    """
    Attach the PlayerResource (API endpoint + Swagger docs) to the given Flask app
    :param app: The app to create the endpoint for
    :return: None
    """
    blueprint = Blueprint('api_spell', __name__)
    api = Api(blueprint)
    api.add_resource(SpellResource, '/api/spell')
    api.add_resource(SpellListResource, '/api/spell/list')
    app.register_blueprint(blueprint, url_prefix='/')  # Relative to api.add_resource path
    add_swagger(api)
