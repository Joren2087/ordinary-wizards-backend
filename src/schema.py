from flask_restful_swagger_3 import Schema

"""
These are generic schemas that can be used to define the JSON response for a successful or failed request throughout the API
"""


class SuccessSchema(Schema):
    """
    Defines the JSON response for a successful request
    """

    type = 'object'
    properties = {
        'status': {
            'type': 'string'
        },
        'message': {
            'type': 'string'
        }
    }
    required = ['status', 'message']

    def __init__(self, message: str="success"):
        super().__init__(status="success", message=message)


class ErrorSchema(Schema):
    """
    Defines the JSON response for a failed request
    """

    type = 'object'
    properties = {
        'status': {
            'type': 'string'
        },
        'message': {
            'type': 'string'
        }
    }
    required = ['status', 'message']

    def __init__(self, message: str="error"):
        super().__init__(status="error", message=message)


class IntArraySchema(Schema):
    """
    Defines the JSON response for a list of integers
    """

    type = 'array'
    items = {
        'type': 'integer'
    }
    required = []

    def __init__(self, items: list[int]):
        super().__init__(items=items)

class ArraySchema(Schema):
    """
    Defines the JSON response for a list of integers
    """

    type = 'array'
    items = {
        'type': 'string'
    }
    required = []

    def __init__(self, items: list[str]):
        super().__init__(items=items)