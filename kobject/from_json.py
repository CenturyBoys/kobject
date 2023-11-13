"""
Package to  helper to decode json in a class instance
"""

import json
from enum import Enum
from inspect import isclass
from typing import Type, Any, Callable

from kobject.common import T, InheritanceFieldMeta


def _resolve_list(_type: Type, attr_value: Any) -> list:
    attr_value_new = []
    for attr_value_item in attr_value:
        for sub_types in _type.__args__:
            try:
                attr_value_new.append(
                    JSONDecoder.type_caster(
                        attr_type=sub_types,
                        attr_value=attr_value_item,
                    )
                )
                break
            finally:
                continue
    return attr_value_new


def _resolve_tuple(_type: Type, attr_value: Any):
    attr_value_new = []
    for attr_value_item, attr_type in zip(attr_value, _type.__args__):
        attr_value_new.append(
            JSONDecoder.type_caster(
                attr_type=attr_type,
                attr_value=attr_value_item,
            )
        )
    return tuple(attr_value_new)


def _resolve_dict(_type: Type, attr_value: Any):
    attr_value_new = {}
    for key, value in attr_value.items():
        attr_value_new.update(
            {
                JSONDecoder.type_caster(
                    attr_type=_type.__args__[0],
                    attr_value=key,
                ): JSONDecoder.type_caster(
                    attr_type=_type.__args__[1],
                    attr_value=value,
                )
            }
        )
    return attr_value_new


class FromJSON(InheritanceFieldMeta):
    """
    FromJSON will provide a from_json() and a from_dict() methods to instantiate your objects
    """

    __from_json_custom_exception__: Type[Exception] = None

    @classmethod
    def set_content_check_custom_exception(cls, exception: Type[Exception]):
        """
        Will change de default JSONDecodeError error
        """
        cls.__from_json_custom_exception__ = exception

    @staticmethod
    def set_decoder_resolver(attr_type: Type[Any], resolver_callback: Callable):
        """
        Register a resolver for a class or subclass\n

        attr_type: int,str,bool,float or any other class\n
        resolver_callback: lambda function that receives the type and value to be cast.
         Example 'lambda attr_type, value: value'
        """
        JSONDecoder.types_resolver.insert(0, (attr_type, resolver_callback))

    @classmethod
    def from_json(cls: T, payload: bytes) -> Type[T]:
        """
        Returns a class instance by the giving json payload
        """
        try:
            dict_repr = json.loads(payload)
            instance = cls.from_dict(dict_repr=dict_repr)
            return instance
        except TypeError as original_error:
            if cls.__from_json_custom_exception__ is not None:
                raise cls.__from_json_custom_exception__(original_error.args[0])
            raise original_error
        except Exception as original_error:
            if cls.__from_json_custom_exception__ is not None:
                raise cls.__from_json_custom_exception__(  # pylint: disable=E1102
                    f"Invalid content -> {str(payload)}",
                ) from original_error
            raise original_error

    @classmethod
    def from_dict(cls: T, dict_repr: dict) -> Type[T]:  # pylint: disable=R0914
        """
        Returns a class instance by the giving dict representation
        """

        _missing = []

        for field in cls._with_field_map():
            if field.have_default_value:
                continue
            if field.name not in dict_repr:
                _missing.append(field.name)
                continue

            attr_value = dict_repr.get(field.name)
            base_type = JSONDecoder.get_base_type(attr_type=field.annotation)

            if issubclass(base_type, list | tuple | dict) is False:
                dict_repr[field.name] = JSONDecoder.type_caster(
                    attr_type=field.annotation, attr_value=attr_value
                )

            elif issubclass(base_type, list) and isinstance(attr_value, list):
                dict_repr[field.name] = _resolve_list(
                    _type=field.annotation, attr_value=attr_value
                )

            elif issubclass(base_type, tuple) and isinstance(attr_value, list):
                dict_repr[field.name] = _resolve_tuple(
                    _type=field.annotation, attr_value=attr_value
                )

            elif issubclass(base_type, dict) and isinstance(attr_value, dict):
                dict_repr[field.name] = _resolve_dict(
                    _type=field.annotation, attr_value=attr_value
                )

        if _missing:
            raise TypeError(
                f"Missing content -> The fallow attr are not presente {', '.join(_missing)}"
            )
        return cls(**dict_repr)


class JSONDecoder:
    """
    Implementation tyo decode json in to class instance inspired by json.JSONEncoder
    """

    types_resolver = []

    @staticmethod
    def get_base_type(attr_type):
        """
        Returns the base type if the parameter attr_type has __original__ attribute
        """
        if hasattr(attr_type, "__origin__"):
            attr_type = attr_type.__origin__
        return attr_type

    @classmethod
    def type_caster(cls, attr_type, attr_value):  # pylint: disable=R1710
        """
        Returns the result of cast attribute type for the attribute type
        """
        for map_attr_type, resolver in cls.types_resolver:
            if isclass(attr_type) and issubclass(attr_type, map_attr_type):
                return resolver(attr_type, attr_value)
        return attr_value


FromJSON.set_decoder_resolver(bool, lambda attr_type, value: value)
FromJSON.set_decoder_resolver(
    float, lambda attr_type, value: float(value) if isinstance(value, int) else value
)
FromJSON.set_decoder_resolver(int, lambda attr_type, value: value)
FromJSON.set_decoder_resolver(str, lambda attr_type, value: value)
FromJSON.set_decoder_resolver(
    FromJSON,
    lambda attr_type, value: attr_type.from_dict(value)
    if isinstance(value, dict)
    else value,
)
FromJSON.set_decoder_resolver(
    Enum,
    lambda attr_type, value: attr_type(value)
    if any(value is i.value for i in attr_type)
    else value,
)
