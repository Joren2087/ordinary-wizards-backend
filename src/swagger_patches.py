"""
This file patches all the stupid and broken stuff in the swagger module
"""

from flask_restful_swagger_3 import Schema, REGISTRY_SCHEMA


def check_type(self, type_, key, value):
        """
        Copied from original flask_restful_swagger_3 source code, but fixed the broken parts that were
        incomplete with our own implementation/usage
        """
        if type_:
            if type_ == 'array':
                if not isinstance(value, list):
                    raise ValueError(f'The attribute "{key}" must be a list, but was "{type(value)}')
                temp = self.properties[key]
                if not isinstance(temp, dict):
                    return # no schema to check
                cls = temp.get('items')
                if cls and hasattr(cls, '__name__') and cls.__name__ in REGISTRY_SCHEMA:
                    if hasattr(cls, '_abstract_class') and cls._abstract_class:
                        for v in value:
                            if v.__class__.__name__ not in REGISTRY_SCHEMA:
                                raise ValueError(f'{v.__name__} is not a registered schema')
                            if not isinstance(v, cls):
                                raise ValueError(f'The schema {v.__name__} should be a subclass of {cls.__name__}')

                            # TODO , check type on subclass



                    elif cls.type == 'object':
                        for v in value:
                            cls(**v)
                    else:
                        for v in value:
                            self.check_type(cls.type,  key, v)
            if value is None:
                b = self.properties[key]
                if hasattr(b, 'properties'):
                    b = b.properties
                if not b.get('nullable', True):
                    raise ValueError(f'The attribute "{key}" must not be null')
                else:
                    return # no need to check further

            if type_ == 'integer' and not isinstance(value, int):
                raise ValueError(f'The attribute "{key}" must be an int, but was "{type(value)}"')
            if type_ == 'number' and not isinstance(value, int) and not isinstance(value, float):
                raise ValueError(
                    f'The attribute "{key}" must be an int or float, but was "{type(value)}"')
            if type_ == 'string' and not isinstance(value, str):
                raise ValueError(f'The attribute "{key}" must be a string, but was "{type(value)}"')
            if type_ == 'boolean' and not isinstance(value, bool):
                raise ValueError(f'The attribute "{key}" must be a bool, but was "{type(value)}"')

# Monkey patch the broken check_type method
Schema.check_type = check_type

def __init__(self, **kwargs):
    # super().__init__(**kwargs)
    check_required = kwargs.pop('_check_requirements', False)

    if self.properties:
        for k, v in kwargs.items():
            if k not in self.properties:
                raise ValueError(
                    'The model "{0}" does not have an attribute "{1}"'.format(self.__class__.__name__, k))
            if type(self.properties[k]) == type:
                if self.properties[k].type == 'object':
                    self.properties[k](**v if v else {})
                self.prop = self.properties[k].definitions()
            else:
                self.prop = self.properties[k]

            nullable = self.get_boolean_attribute('nullable')
            load_only = self.get_boolean_attribute('load_only')
            dump_only = self.get_boolean_attribute('dump_only')
            if load_only and dump_only:
                raise TypeError('A value can\'t be load_only and dump_only in the same schema')

            type_ = self.prop.get('type', None)
            format_ = self.prop.get('format', None)

            if not (nullable and v is None):
                self.check_type(type_, k, v)
                if 'enum' in self.prop:
                    if type(self.prop['enum']) not in [set, list, tuple]:
                        raise TypeError(f"'enum' must be 'list', 'set' or 'tuple',"
                                        f"but was {type(self.prop['enum'])}")
                    for item in list(self.prop['enum']):
                        self.check_type(type_, 'enum', item)
                    if v not in self.prop['enum']:
                        raise ValueError(f"{k} must have {' or '.join(self.prop['enum'])} but have {v}")
                # Just fk it, we don't need to check format - it's broke af anyway
                #if v:  # NoneType check - if v is None, we don't need to check format
                #    self.check_format(type_, format_, v)

            if load_only:
                del self[k]
                continue

            self[k] = v

    if hasattr(self, 'required') and check_required:
        self.required = list(self.required)
        for key in self.required:
            if key not in kwargs:
                raise ValueError('The attribute "{0}" is required'.format(key))


# Monkey patch the broken __init__ method
Schema.__init__ = __init__

# Default docstring for Schema
Schema.__doc__ = """
    A schema that represents the model in JSON format.
    """


def summary(summary: str):
    """
    A decorator to add a summary to a method
    :param summary: The summary of the method
    :param description: The description of the method
    :return: The method with the summary and description
    """
    def wrapper(func):
        if "__summary" in func.__dict__:
            func.__summary.append(summary)
        else:
            func.__summary = [summary]

        return func
    return wrapper