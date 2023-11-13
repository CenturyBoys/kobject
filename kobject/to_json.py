"""
Package to helper to encode class in json
"""

import json
from typing import Callable

from kobject.common import InheritanceFieldMeta


class ToJSON(InheritanceFieldMeta):
    """
    ToJSON will provide a dict() and a to_json() methods for your class
    """

    @staticmethod
    def set_encoder_resolver(attr_type, resolver_callback: Callable):
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

        for field in self._with_field_map():
            attr_value = getattr(self, field.name)
            if not isinstance(attr_value, list | tuple | dict):
                _dict_representation.update(
                    {field.name: JSONEncoder.default(attr_value)}
                )
                continue
            if isinstance(attr_value, list | tuple):
                attr_value_new = []
                for attr_value_item in attr_value:
                    attr_value_new.append(JSONEncoder.default(attr_value_item))
                _dict_representation.update({field.name: attr_value_new})
            else:
                attr_value_new = {}
                for key, value in attr_value.items():
                    attr_value_new.update(
                        {JSONEncoder.default(key): JSONEncoder.default(value)}
                    )
                _dict_representation.update({field.name: attr_value_new})

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

    @staticmethod
    def get_type(attr_type):
        """
        Returns the type or subtypes of giving attribute type
        """
        attr_type = attr_type.__origin__
        return attr_type

    @classmethod
    def default(cls, obj):  # pylint: disable=W0221
        if isinstance(obj, ToJSON):
            return obj.dict()
        for map_attr_type, resolver in cls.base_types_resolver.items():
            if isinstance(obj, map_attr_type):
                return resolver(obj)
        return obj
