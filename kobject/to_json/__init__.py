"""
Package to helper to encode class in json
"""

import json
import typing


class ToJSON:
    """
    ToJSON will provide a dict() and a to_json() methods for your class
    """

    @staticmethod
    def set_encoder_resolver(attr_type, resolver_callback: typing.Callable):
        """
        Register a resolver for a class or subclass
        attr_type: int,str,bool,float or any other class
        resolver_callback: lambda function that receives the value to be cast.
         Example 'lambda value: value'
        """
        JSONEncoder.base_types_resolver.update({attr_type: resolver_callback})

    def dict(self):
        """
        Returns dict representation of your object
        """
        _dict_representation = {}
        _annotations = typing.get_type_hints(type(self))

        del _annotations["_Kobject__custom_exception"]

        if "_FromJSON__custom_exception" in _annotations:
            del _annotations["_FromJSON__custom_exception"]

        for attr in _annotations:
            attr_value = object.__getattribute__(self, attr)
            _dict_representation.update({attr: attr_value})
        return _dict_representation

    def to_json(self) -> bytes:
        """
        Returns json of your object
        """
        dict_repr = self.dict()
        json_bytes = json.dumps(dict_repr, default=JSONEncoder.default)
        return json_bytes.encode()


class JSONEncoder(json.JSONEncoder):
    """
    Self implementation for default json.JSONEncoder
    """

    base_types_resolver = {}

    @classmethod
    def default(cls, obj):  # pylint: disable=W0221
        if isinstance(obj, ToJSON):
            return obj.dict()
        for map_attr_type, resolver in cls.base_types_resolver.items():
            if isinstance(obj, map_attr_type):
                return resolver(obj)
        return obj
