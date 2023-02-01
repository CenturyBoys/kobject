"""
Package to  helper to decode json in a class instance
"""

import inspect
import json
import typing


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
        JSONDecoder.types_resolver.update({attr_type: resolver_callback})

    @classmethod
    def from_json(cls: T, payload: bytes) -> typing.Type[T]:
        """
        Returns a class instance by the giving json payload
        """
        try:
            dict_repr = json.loads(payload)
        except Exception as original_error:
            if cls.__custom_exception is not None:
                raise cls.__custom_exception(  # pylint: disable=E1102
                    f"Invalid content -> {str(payload)}",
                ) from original_error
            raise original_error
        instance = cls.from_dict(dict_repr=dict_repr)
        return instance

    @classmethod
    def from_dict(cls: T, dict_repr: dict) -> typing.Type[T]:
        """
        Returns a class instance by the giving dict representation
        """

        _annotations = typing.get_type_hints(cls)

        del _annotations["_Kobject__custom_exception"]
        del _annotations["_FromJSON__custom_exception"]

        for attr, attr_type in _annotations.items():
            attr_value = dict_repr.get(attr)
            casted_value = JSONDecoder.type_caster(
                attr_type=attr_type, attr_value=attr_value
            )
            if casted_value is not None:
                dict_repr[attr] = casted_value
                continue

            attr_type, sub_type = JSONDecoder.get_type(attr_type=attr_type)

            attr_value_new = []
            for attr_value_item in attr_value:
                attr_value_new.append(
                    JSONDecoder.type_caster(
                        attr_type=sub_type, attr_value=attr_value_item
                    )
                )
            dict_repr[attr] = attr_type(attr_value_new)
        instance = cls(**dict_repr)
        return instance


class JSONDecoder:
    """
    Implementation tyo decode json in to class instance inspired by json.JSONEncoder
    """

    types_resolver = {
        int: lambda attr_type, value: value,
        str: lambda attr_type, value: value,
        bool: lambda attr_type, value: value,
        float: lambda attr_type, value: value,
        FromJSON: lambda attr_type, value: attr_type.from_dict(value),
    }

    @staticmethod
    def get_type(attr_type):
        """
        Returns the type or subtypes of giving attribute type
        """
        sub_type = attr_type.__args__[0]
        attr_type = attr_type.__origin__
        return attr_type, sub_type

    @classmethod
    def type_caster(cls, attr_type, attr_value):
        """
        Returns the result of cast attribute type for the attribute type
        """
        for map_attr_type, resolver in cls.types_resolver.items():
            if inspect.isclass(attr_type) and issubclass(attr_type, map_attr_type):
                return resolver(attr_type, attr_value)
        return None
