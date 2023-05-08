"""
Package to  helper to decode json in a class instance
"""

import inspect
import json
import typing
from enum import Enum

T = typing.TypeVar("T")


class FromJSON:
    """
    FromJSON will provide a from_json() and a from_dict() methods to instantiate your objects
    """

    __custom_exception: typing.Type[Exception] = None

    @classmethod
    def set_custom_exception(cls, exception: typing.Type[Exception]):
        """
        Will change de default JSONDecodeError error
        """
        cls.__custom_exception = exception

    @staticmethod
    def set_decoder_resolver(attr_type, resolver_callback: typing.Callable):
        """
        Register a resolver for a class or subclass\n

        attr_type: int,str,bool,float or any other class\n
        resolver_callback: lambda function that receives the type and value to be cast.
         Example 'lambda attr_type, value: value'
        """
        JSONDecoder.types_resolver.insert(0, (attr_type, resolver_callback))

    @classmethod
    def from_json(cls: T, payload: bytes) -> typing.Type[T]:
        """
        Returns a class instance by the giving json payload
        """
        try:
            dict_repr = json.loads(payload)
            instance = cls.from_dict(dict_repr=dict_repr)
            return instance
        except Exception as original_error:
            if cls.__custom_exception is not None:
                raise cls.__custom_exception(  # pylint: disable=E1102
                    f"Invalid content -> {str(payload)}",
                ) from original_error
            raise original_error

    @staticmethod
    def attribute_has_default_value(attr: str, attr_metadata: dict) -> bool:
        """
        Validate that the attribute has default values
        """
        default_value = attr_metadata.get(attr).default
        return default_value != inspect._empty  # pylint: disable=W0212

    @classmethod
    def resolve_type(cls, attr_type, attr_value):
        """
        Cast attr value to attr type
        """
        try:
            return JSONDecoder.type_caster(attr_type, attr_value)
        except TypeError as exception:
            message = f"Unable to cast value {attr_value} of type {type(attr_value)} to {attr_type}"
            if cls.__custom_exception:
                raise cls.__custom_exception(  # pylint: disable=E1102
                    message
                ) from exception
            raise TypeError(message) from exception

    @classmethod
    def from_dict(cls: T, dict_repr: dict) -> typing.Type[T]:  # pylint: disable=R0914
        """
        Returns a class instance by the giving dict representation
        """

        _annotations = typing.get_type_hints(cls)
        _annotations_meta = dict(inspect.signature(cls.__init__).parameters.items())
        _missing = []

        del _annotations["_Kobject__custom_exception"]
        del _annotations["_FromJSON__custom_exception"]

        for attr, attr_type in _annotations.items():
            has_default_value = cls.attribute_has_default_value(attr, _annotations_meta)
            attr_not_present = attr not in dict_repr
            if attr_not_present and has_default_value:
                continue
            if attr_not_present and not has_default_value:
                _missing.append(attr)
                continue
            attr_value = dict_repr.get(attr)
            is_attr_a_iterable = issubclass(
                JSONDecoder.get_base_type(attr_type=attr_type), (list, tuple)
            )
            is_value_a_iterable = isinstance(attr_value, (list, tuple))
            if not is_attr_a_iterable or (
                is_attr_a_iterable and not is_value_a_iterable
            ):
                dict_repr[attr] = cls.resolve_type(
                    attr_type=attr_type, attr_value=attr_value
                )
                continue

            attr_type, sub_type = JSONDecoder.get_type(attr_type=attr_type)

            attr_value_new = []
            for attr_value_item in attr_value:
                attr_value_new.append(
                    cls.resolve_type(attr_type=sub_type, attr_value=attr_value_item)
                )
            dict_repr[attr] = attr_type(attr_value_new)
        if _missing:
            message = f"Missing content -> The fallow attr are not presente {', '.join(_missing)}"
            if cls.__custom_exception:
                raise cls.__custom_exception(message)  # pylint: disable=E1102
            raise TypeError(message)
        return cls(**dict_repr)


class JSONDecoder:
    """
    Implementation tyo decode json in to class instance inspired by json.JSONEncoder
    """

    types_resolver = []

    @staticmethod
    def get_type(attr_type):
        """
        Returns the type or subtypes of giving attribute type
        """
        sub_type = attr_type.__args__[0]
        attr_type = attr_type.__origin__
        return attr_type, sub_type

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
            if inspect.isclass(attr_type) and issubclass(attr_type, map_attr_type):
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
