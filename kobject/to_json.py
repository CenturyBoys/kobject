import json
from inspect import Signature
from typing import List, Callable

from kobject.common import FieldMeta


class ToJSON:
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

    __field_map__: list[FieldMeta] = None

    @classmethod
    def __with_field_map(cls) -> List[FieldMeta]:
        if cls.__field_map__ is None:
            cls.__field_map__ = []
            for param in Signature.from_callable(cls).parameters.values():
                cls.__field_map__.append(
                    FieldMeta.new_one(
                        name=param.name,
                        annotation=param.annotation,
                        value=param.default,
                    )
                )
        return cls.__field_map__

    def dict(self):
        """
        Returns dict representation of your object
        """
        _dict_representation = {}

        for field in self.__with_field_map():
            attr_value = object.__getattribute__(self, field.name)
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
                continue
            if isinstance(attr_value, dict):
                attr_value_new = {}
                for key, value in attr_value.items():
                    attr_value_new.update(
                        {JSONEncoder.default(key): JSONEncoder.default(value)}
                    )
                continue

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
