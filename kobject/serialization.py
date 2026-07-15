"""JSON serialization and deserialization for Kobject."""

from __future__ import annotations

import json
import threading
import types
from collections.abc import Callable
from inspect import isclass
from typing import Any, ClassVar, Union, get_args, get_origin

from kobject._compat import is_literal


def is_union(attr_type: type | type[Any]) -> bool:
    """Check if attr_type is a Union type."""
    return get_origin(attr_type) is Union or isinstance(attr_type, types.UnionType)


# Cache of detected discriminators keyed by the union type. The result is a pure
# function of the union members, so caching never leaks test state.
_discriminator_cache: dict[Any, tuple[str, dict[Any, type[Any]]] | None] = {}


def _get_union_discriminator(
    attr_type: type[Any],
) -> tuple[str, dict[Any, type[Any]]] | None:
    """Detect an automatic tag discriminator for a union of Kobject subclasses.

    A discriminator is a field present on every Kobject member whose annotation
    is a typing.Literal with tag values that are unique across members. Returns
    ``(field_name, {tag_value: member})`` or ``None`` when the union has no such
    unambiguous tag field.
    """
    if attr_type in _discriminator_cache:
        return _discriminator_cache[attr_type]

    from kobject.core import Kobject

    members = [m for m in get_args(attr_type) if isclass(m) and issubclass(m, Kobject)]
    result: tuple[str, dict[Any, type[Any]]] | None = None
    if len(members) >= 2:
        for meta in members[0]._with_field_map():
            if not is_literal(meta.annotation):
                continue
            tag_map: dict[Any, type[Any]] = {}
            ok = True
            for member in members:
                field_meta = next(
                    (f for f in member._with_field_map() if f.name == meta.name),
                    None,
                )
                if field_meta is None or not is_literal(field_meta.annotation):
                    ok = False
                    break
                for tag in get_args(field_meta.annotation):
                    if tag in tag_map:  # tag reused across members -> ambiguous
                        ok = False
                        break
                    tag_map[tag] = member
                if not ok:
                    break
            if ok and tag_map:
                result = (meta.name, tag_map)
                break

    _discriminator_cache[attr_type] = result
    return result


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
        if is_union(attr_type):
            return cls._cast_union(attr_type, attr_value)
        for map_attr_type, resolver in cls.types_resolver:
            if _checker(attr_type, map_attr_type):
                return resolver(attr_type, attr_value)
        return attr_value

    @classmethod
    def _cast_union(cls, attr_type: type[Any], attr_value: Any) -> Any:
        """
        Cast a value for a Union type.

        When the union is a tagged discriminated union (every Kobject member
        shares a Literal-typed field with unique tag values), the tag in the
        payload authoritatively selects the member. Otherwise each member is
        tried in declaration order and the first that successfully deserializes
        wins; if more than one could match, the first declared one wins.
        """
        # Local imports to avoid circular imports (same pattern as JSONEncoder).
        from kobject.fields import FieldMeta
        from kobject.validation import _validate_field_value

        if isinstance(attr_value, dict):
            discriminator = _get_union_discriminator(attr_type)
            if discriminator is not None:
                field_name, tag_map = discriminator
                member = tag_map.get(attr_value.get(field_name))
                if member is not None:
                    # Tag selects the member authoritatively: commit to it so a
                    # malformed payload reports an error against the right type
                    # instead of silently falling through to another member.
                    return cls.type_caster(member, attr_value)

        for member in get_args(attr_type):
            try:
                decoded = cls.type_caster(member, attr_value)
            except Exception:
                continue
            if _validate_field_value(decoded, FieldMeta.get_generic_field_meta(member)):
                return decoded
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


def _resolve_set(_type: type[Any], attr_value: Any) -> set[Any]:
    """Resolve a set type from JSON (array)."""
    attr_value_new = set()
    for attr_value_item in attr_value:
        for sub_types in _type.__args__:
            result = JSONDecoder.type_caster(
                attr_type=sub_types,
                attr_value=attr_value_item,
            )
            attr_value_new.add(result)
            break
    return attr_value_new


def _resolve_dict(_type: type[Any], attr_value: dict[Any, Any]) -> dict[Any, Any]:
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
