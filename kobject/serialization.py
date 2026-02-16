"""JSON serialization and deserialization for Kobject."""

from __future__ import annotations

import json
import threading
import types
from collections.abc import Callable
from inspect import isclass
from typing import Any, ClassVar, Union, get_args, get_origin


def is_union(attr_type: type | type[Any]) -> bool:
    """Check if attr_type is a Union type."""
    return get_origin(attr_type) is Union or isinstance(attr_type, types.UnionType)


def _checker(
    attr_type: type | type[Any], reference: type | type[Any] | types.UnionType
) -> bool:
    """Check if attr_type is or contains a subclass of reference."""
    if is_union(attr_type):
        return any(
            isinstance(t, type) and issubclass(t, reference)
            for t in get_args(attr_type)
        )
    return isclass(attr_type) and issubclass(attr_type, reference)


class JSONDecoder:
    """
    Implementation to decode JSON into class instance, inspired by json.JSONEncoder.
    """

    _lock: ClassVar[threading.Lock] = threading.Lock()
    types_resolver: ClassVar[list[tuple[type, Callable[..., Any]]]] = []

    @staticmethod
    def get_base_type(attr_type: type[Any]) -> type[Any]:
        """
        Returns the base type if the parameter attr_type has __origin__ attribute.
        """
        if hasattr(attr_type, "__origin__"):
            attr_type = attr_type.__origin__
        return attr_type

    @classmethod
    def register_resolver(cls, attr_type: type, callback: Callable[..., Any]) -> None:
        """Register a resolver with thread safety."""
        with cls._lock:
            cls.types_resolver.insert(0, (attr_type, callback))

    @classmethod
    def type_caster(cls, attr_type: type[Any], attr_value: Any) -> Any:
        """
        Returns the result of casting attribute value to the attribute type.
        """
        for map_attr_type, resolver in cls.types_resolver:
            if _checker(attr_type, map_attr_type):
                for _type in get_args(attr_type):
                    if issubclass(_type, map_attr_type):
                        return resolver(_type, attr_value)
                return resolver(attr_type, attr_value)
        return attr_value


class JSONEncoder(json.JSONEncoder):
    """
    Custom implementation for default json.JSONEncoder.
    """

    _lock: ClassVar[threading.Lock] = threading.Lock()
    base_types_resolver: ClassVar[dict[type, list[Any]]] = {}

    @staticmethod
    def get_type(attr_type: type[Any]) -> type[Any]:
        """
        Returns the type or subtypes of given attribute type.
        """
        attr_type = attr_type.__origin__
        return attr_type

    @classmethod
    def register_resolver(
        cls, attr_type: type, callback: Callable[..., Any], on_dict: bool = True
    ) -> None:
        """Register a resolver with thread safety."""
        with cls._lock:
            cls.base_types_resolver[attr_type] = [callback, on_dict]

    @classmethod
    def default(cls, obj: Any) -> Any:
        """
        Resolve object to JSON-parsable dict using registered resolvers,
        excluding on_dict option. Kobject.set_encoder_resolver()
        """
        # Import here to avoid circular imports
        from kobject.core import Kobject

        if isinstance(obj, Kobject):
            return obj.dict()
        for map_attr_type, resolver in cls.base_types_resolver.items():
            if isinstance(obj, map_attr_type):
                return resolver[0](obj)
        return obj

    @classmethod
    def dict_default(cls, obj: Any) -> Any:
        """Resolve object to dict using registered resolvers."""
        # Import here to avoid circular imports
        from kobject.core import Kobject

        if isinstance(obj, Kobject):
            return obj.dict()
        for map_attr_type, resolver in cls.base_types_resolver.items():
            if isinstance(obj, map_attr_type) and resolver[1]:
                return resolver[0](obj)
        return obj


def _resolve_list(_type: type[Any], attr_value: Any) -> list[Any]:
    """Resolve a list type from JSON."""
    attr_value_new = []
    for attr_value_item in attr_value:
        for sub_types in _type.__args__:
            result = JSONDecoder.type_caster(
                attr_type=sub_types,
                attr_value=attr_value_item,
            )
            attr_value_new.append(result)
            break  # Use first matching type
    return attr_value_new


def _resolve_tuple(_type: type[Any], attr_value: Any) -> tuple[Any, ...]:
    """Resolve a tuple type from JSON."""
    attr_value_new = []
    for attr_value_item, attr_type in zip(attr_value, _type.__args__, strict=False):
        attr_value_new.append(
            JSONDecoder.type_caster(
                attr_type=attr_type,
                attr_value=attr_value_item,
            )
        )
    return tuple(attr_value_new)


def _resolve_dict(_type: type[Any], attr_value: Any) -> dict[Any, Any]:
    """Resolve a dict type from JSON."""
    _typed_dict = hasattr(_type, "__args__")
    if not _typed_dict:
        return attr_value

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
