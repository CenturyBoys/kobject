"""Compatibility helpers to avoid private Python imports."""

from __future__ import annotations

import types
from inspect import Parameter
from typing import Any, Union, get_origin

EMPTY = Parameter.empty


def is_generic_alias(annotation: Any) -> bool:
    """Check if annotation is a generic alias (List[int], Dict[str, int], etc.)."""
    return hasattr(annotation, "__origin__")


def is_special_form_union(annotation: Any) -> bool:
    """Check if annotation is Union or Optional."""
    origin = get_origin(annotation)
    return origin is Union


def is_union_type(annotation: Any) -> bool:
    """Check for both typing.Union and types.UnionType (X | Y syntax)."""
    origin = get_origin(annotation)
    return origin is Union or isinstance(annotation, types.UnionType)
