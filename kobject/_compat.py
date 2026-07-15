"""Compatibility helpers to avoid private Python imports."""

from __future__ import annotations

import types
from inspect import Parameter
from typing import Any, Literal, TypeVar, Union, get_args, get_origin

EMPTY = Parameter.empty


def is_generic_alias(annotation: Any) -> bool:
    """Check if annotation is a generic alias or union type (X | Y)."""
    return hasattr(annotation, "__origin__") or isinstance(annotation, types.UnionType)


def is_literal(annotation: Any) -> bool:
    """Check if annotation is a typing.Literal[...] form."""
    return get_origin(annotation) is Literal


def is_type_var(annotation: Any) -> bool:
    """Check if annotation is a bare TypeVar."""
    return isinstance(annotation, TypeVar)


def substitute_type_vars(annotation: Any, mapping: dict[Any, Any]) -> Any:
    """Recursively replace TypeVars in an annotation using ``mapping``.

    Unbound TypeVars (absent from ``mapping``) collapse to ``Any``. Nested
    generic forms (``list[T]``, ``dict[K, V]``, ``T | None``, ``tuple[T, ...]``)
    are rebuilt with their arguments substituted.
    """
    if isinstance(annotation, TypeVar):
        return mapping.get(annotation, Any)

    args = get_args(annotation)
    if not args:
        return annotation

    new_args = tuple(substitute_type_vars(a, mapping) for a in args)
    if new_args == args:
        return annotation

    if get_origin(annotation) is Union or isinstance(annotation, types.UnionType):
        result = new_args[0]
        for arg in new_args[1:]:
            result = result | arg
        return result

    origin = get_origin(annotation)
    return origin[new_args if len(new_args) > 1 else new_args[0]]


def is_special_form_union(annotation: Any) -> bool:
    """Check if annotation is Union, Optional, or X | Y syntax."""
    origin = get_origin(annotation)
    return origin is Union or isinstance(annotation, types.UnionType)
