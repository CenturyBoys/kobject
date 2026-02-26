"""Validation functions for Kobject type checking."""

from __future__ import annotations

from typing import Any

from kobject._compat import is_generic_alias, is_special_form_union
from kobject.fields import FieldMeta


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


def _validate_field_value(value: Any, field: FieldMeta) -> bool:
    """Validate a field value against its type annotation."""
    if value == field.default or field.annotation in (Ellipsis, Any):
        _is_valid = True

    elif is_generic_alias(field.annotation) is False:
        _is_valid = isinstance(value, field.annotation)

    elif is_special_form_union(field.annotation):
        _is_valid = _validate_special_form(field, value)

    elif not isinstance(
        value,
        field.annotation.__origin__,
    ):
        _is_valid = False

    elif issubclass(field.annotation.__origin__, dict):
        _is_valid = _validate_dict(field, value)

    elif issubclass(field.annotation.__origin__, list):
        _is_valid = _validate_list(field, value)

    elif issubclass(field.annotation.__origin__, tuple):
        _is_valid = _validate_tuple(field, value)

    else:
        # For other generic types without specific handlers, accept the value
        # as long as it passes the isinstance check above (e.g., Coroutine, Callable)
        _is_valid = True

    assert isinstance(_is_valid, bool)

    return _is_valid
