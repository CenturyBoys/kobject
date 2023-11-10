import json
from enum import Enum
from inspect import isclass, Signature
from typing import List, Type, Any, Callable

from kobject.common import FieldMeta, T


class FromJSON:
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
        except Exception as original_error:
            if cls.__from_json_custom_exception__ is not None:
                raise cls.__from_json_custom_exception__(  # pylint: disable=E1102
                    f"Invalid content -> {str(payload)}",
                ) from original_error
            raise original_error

    @classmethod
    def resolve_type(cls, attr_type, attr_value):
        """
        Cast attr value to attr type
        """
        try:
            return JSONDecoder.type_caster(attr_type, attr_value)
        except TypeError as exception:
            message = f"Unable to cast value {attr_value} of type {type(attr_value)} to {attr_type}"
            if cls.__from_json_custom_exception__:
                raise cls.__from_json_custom_exception__(  # pylint: disable=E1102
                    message
                ) from exception
            raise TypeError(message) from exception

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

    @classmethod
    def from_dict(cls: T, dict_repr: dict) -> Type[T]:  # pylint: disable=R0914
        """
        Returns a class instance by the giving dict representation
        """

        _missing = []

        for field in cls.__with_field_map():
            attr_not_present = field.name not in dict_repr
            if attr_not_present and field.have_default_value:
                continue
            if attr_not_present and not field.have_default_value:
                _missing.append(field.name)
                continue
            attr_value = dict_repr.get(field.name)
            if attr_value == field.default:
                continue

            base_type = JSONDecoder.get_base_type(attr_type=field.annotation)
            is_attr_a_iterable = issubclass(base_type, list | tuple | dict)

            if is_attr_a_iterable is False:
                dict_repr[field.name] = cls.resolve_type(
                    attr_type=field.annotation, attr_value=attr_value
                )
                continue

            if issubclass(base_type, list) and isinstance(attr_value, list):
                attr_value_new = []
                for attr_value_item in attr_value:
                    for sub_types in field.annotation.__args__:
                        try:
                            attr_value_new.append(
                                cls.resolve_type(
                                    attr_type=sub_types,
                                    attr_value=attr_value_item,
                                )
                            )
                            break
                        except:
                            continue
                dict_repr[field.name] = attr_value_new
                continue

            if issubclass(base_type, tuple) and isinstance(attr_value, list):
                attr_value_new = []
                for attr_value, attr_type in zip(attr_value, field.annotation.__args__):
                    attr_value_new.append(
                        cls.resolve_type(
                            attr_type=attr_type,
                            attr_value=attr_value,
                        )
                    )
                dict_repr[field.name] = tuple(attr_value_new)
                continue

            if issubclass(base_type, dict) and isinstance(attr_value, dict):
                attr_value_new = {}
                for key, value in attr_value.items():
                    attr_value_new.update(
                        {
                            cls.resolve_type(
                                attr_type=field.annotation.__args__[0],
                                attr_value=key,
                            ): cls.resolve_type(
                                attr_type=field.annotation.__args__[1],
                                attr_value=value,
                            )
                        }
                    )
                dict_repr[field.name] = attr_value_new
                continue

        if _missing:
            message = f"Missing content -> The fallow attr are not presente {', '.join(_missing)}"
            if cls.__from_json_custom_exception__:
                raise cls.__from_json_custom_exception__(
                    message
                )  # pylint: disable=E1102
            raise TypeError(message)
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
    if any(value == i.value for i in attr_type)
    else value,
)
