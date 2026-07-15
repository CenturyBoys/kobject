"""Validation functions for Kobject type checking."""

from __future__ import annotations

from typing import Any, get_args, get_origin

from kobject._compat import (
    is_generic_alias,
    is_literal,
    is_special_form_union,
    is_type_var,
    substitute_type_vars,
)
from kobject.fields import FieldMeta


def _is_kobject_generic(annotation: Any) -> bool:
    """Check if annotation is a parametrized generic Kobject subclass (Box[int])."""
    from kobject.core import Kobject

    origin = get_origin(annotation)
    return (
        isinstance(origin, type)
        and issubclass(origin, Kobject)
        and bool(getattr(origin, "__parameters__", ()))
    )


def _validate_generic_kobject(field: FieldMeta, value: Any) -> bool:
    """Validate a parametrized generic Kobject field by substituting its TypeVars."""
    origin: Any = get_origin(field.annotation)
    mapping = dict(zip(origin.__parameters__, get_args(field.annotation), strict=False))
    for sub_field in origin._with_field_map():
        sub_annotation = substitute_type_vars(sub_field.annotation, mapping)
        if (
            _validate_field_value(
                getattr(value, sub_field.name),
                FieldMeta.get_generic_field_meta(sub_annotation),
            )
            is False
        ):
            return False
    return True


def _validate_literal(value: Any, args: tuple[Any, ...]) -> bool:
    """Validate a Literal type field.

    Match on equality *and* type identity so the True == 1 / False == 0
    pitfall does not let a bool satisfy Literal[1] (or vice versa). PEP 586.
    """
    return any(type(value) is type(arg) and value == arg for arg in args)


def _validate_special_form(field: FieldMeta, value: Any) -> bool:
    """Validate a Union/Optional type field."""
    _is_valid = False
    for options_annotation in field.annotation.__args__:
        if (
            _validate_field_value(
                value, FieldMeta.get_generic_field_meta(options_annotation)
            )
            is True
        ):
            _is_valid = True
            break
    return _is_valid


def _validate_dict(field: FieldMeta, value: Any) -> bool:
    """Validate a Dict type field."""
    for item in value.items():
        for i in range(2):
            if (
                _validate_field_value(
                    item[i],
                    FieldMeta.get_generic_field_meta(field.annotation.__args__[i]),
                )
                is False
            ):
                return False
    return True


def _validate_tuple(field: FieldMeta, value: Any) -> bool:
    """Validate a Tuple type field."""
    if len(field.annotation.__args__) != len(value):
        return False

    for item in value:
        is_item_valid = False
        for type_options in field.annotation.__args__:
            if (
                _validate_field_value(
                    item, FieldMeta.get_generic_field_meta(type_options)
                )
                is True
            ):
                is_item_valid = True
                break
        if is_item_valid is False:
            return is_item_valid
    return True


def _validate_list(field: FieldMeta, value: Any) -> bool:
    """Validate a List type field."""
    for item in value:
        is_item_valid = False
        for type_options in field.annotation.__args__:
            if (
                _validate_field_value(
                    item, FieldMeta.get_generic_field_meta(type_options)
                )
                is True
            ):
                is_item_valid = True
                break
        if is_item_valid is False:
            return is_item_valid
    return True


def _validate_set(field: FieldMeta, value: Any) -> bool:
    """Validate a Set type field."""
    for item in value:
        is_item_valid = False
        for type_options in field.annotation.__args__:
            if (
                _validate_field_value(
                    item, FieldMeta.get_generic_field_meta(type_options)
                )
                is True
            ):
                is_item_valid = True
                break
        if is_item_valid is False:
            return is_item_valid
    return True


def _validate_field_value(value: Any, field: FieldMeta) -> bool:
    """Validate a field value against its type annotation."""
    if is_type_var(field.annotation):
        # Unbound TypeVar (e.g. a generic model used without a binding): accept
        # anything, matching how Any is treated.
        _is_valid = True

    elif value == field.default or field.annotation in (Ellipsis, Any):
        _is_valid = True

    elif is_generic_alias(field.annotation) is False:
        _is_valid = isinstance(value, field.annotation)

    elif is_special_form_union(field.annotation):
        _is_valid = _validate_special_form(field, value)

    elif is_literal(field.annotation):
        _is_valid = _validate_literal(value, get_args(field.annotation))

    elif not isinstance(
        value,
        field.annotation.__origin__,
    ):
        _is_valid = False

    elif _is_kobject_generic(field.annotation):
        _is_valid = _validate_generic_kobject(field, value)

    elif issubclass(field.annotation.__origin__, dict):
        _is_valid = _validate_dict(field, value)

    elif issubclass(field.annotation.__origin__, list):
        _is_valid = _validate_list(field, value)

    elif issubclass(field.annotation.__origin__, tuple):
        _is_valid = _validate_tuple(field, value)

    elif issubclass(field.annotation.__origin__, set):
        _is_valid = _validate_set(field, value)

    else:
        # For other generic types without specific handlers, accept the value
        # as long as it passes the isinstance check above (e.g., Coroutine, Callable)
        _is_valid = True

    assert isinstance(_is_valid, bool)

    return _is_valid
