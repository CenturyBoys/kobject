"""
Object __init__ type validator
"""

# from inspect import _empty
from types import GenericAlias
from typing import (
    _GenericAlias,
    _SpecialForm,
    Type,
    Any,
)

from kobject.common import FieldMeta, InheritanceFieldMeta


def _validate_special_form(field: FieldMeta, value: Any) -> bool:
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


def _validate_tuple_list(field: FieldMeta, value: Any) -> bool:
    for item in value:
        is_item_valid = False
        for type_options in field.annotation.__args__:
            if (
                _validate_field_value(
                    item, FieldMeta.get_generic_field_meta(type_options)
                )
                is True
            ):
                is_item_valid = not is_item_valid
                break
        if is_item_valid is False:
            return is_item_valid
    return True


def _validate_field_value(value: Any, field: FieldMeta) -> bool:
    if value == field.default:
        _is_valid = True

    # elif value is _empty and field.required:
    #     _is_valid = False
    #
    # elif value is _empty and field.required is False:
    #     _is_valid = True

    elif field.annotation in (Ellipsis, Any):
        _is_valid = True

    elif isinstance(field.annotation, GenericAlias | _GenericAlias) is False:
        _is_valid = isinstance(value, field.annotation)

    elif isinstance(field.annotation.__origin__, _SpecialForm):
        _is_valid = _validate_special_form(field, value)

    elif not isinstance(
        value,
        field.annotation.__origin__,
    ):
        _is_valid = False

    elif issubclass(field.annotation.__origin__, dict):
        _is_valid = _validate_dict(field, value)

    else:
        _is_valid = _validate_tuple_list(field, value)

    assert isinstance(_is_valid, bool)

    return _is_valid


class Validator(InheritanceFieldMeta):
    """
    Validator provides a __init__ attribute type checker.
    Will rise a TypeError exception with all validation errors
    Obs: dict values are not allowed
    """

    __custom_exception__: Type[Exception] = None
    __lazy_type_check__: bool = False

    def __post_init__(self):
        self.__validate_model()

    def __validate_model(self):
        _errors = []
        for field in self._with_field_map():
            # When we replace the __post_init__ with __new__ the income arguments cant be not there.
            # value = getattr(self, field.name) if hasattr(self, field.name) else _empty
            if _validate_field_value(getattr(self, field.name), field) is False:
                _errors.append(
                    f"Wrong type for {field.name}:"
                    f" {field.annotation} != '{type(getattr(self, field.name))}'"
                )
                assert isinstance(self.__lazy_type_check__, bool)
                if self.__lazy_type_check__:
                    break
        if _errors:
            exception = self.__custom_exception__
            if self.__custom_exception__ is None:
                exception = TypeError
            raise exception(
                "Class '{}' type error:\n {}".format(
                    self.__class__.__name__, "\n ".join(_errors), values=self.__dict__
                )
            )

    @classmethod
    def set_validation_custom_exception(cls, exception: Type[Exception]):
        """
        Will change de default validation error (TypeError)
        """
        cls.__custom_exception__ = exception

    @classmethod
    def set_lazy_type_check(cls, status: bool):
        """
        Will change the type  (TypeError)
        """
        cls.__lazy_type_check__ = status

    def __repr__(self):
        class_name = self.__class__.__name__
        values = [
            f"{field_map.name}={getattr(self, field_map.name)}"
            for field_map in self._with_field_map()
        ]
        return f"<{class_name} ({', '.join(values)})>"

    def __str__(self):
        return self.__repr__()
