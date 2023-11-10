from inspect import Signature, _empty
from types import GenericAlias
from typing import (
    _SpecialGenericAlias,
    _GenericAlias,
    _UnionGenericAlias,
    _SpecialForm,
    Type,
    Any,
    List,
)

from kobject.common import FieldMeta


def _validate_field_value(value: Any, field: FieldMeta) -> bool:
    if value == field.default:
        return True

    if value is _empty and field.required:
        return False

    if value is _empty and field.required is False:
        value = field.default

    if field.annotation == Ellipsis:
        return True

    if isinstance(field.annotation, GenericAlias | _GenericAlias) is False:
        return isinstance(value, field.annotation)

    if isinstance(field.annotation.__origin__, _SpecialForm):
        for options_annotation in field.annotation.__args__:
            if _validate_field_value(
                value, FieldMeta.get_generic_field_meta(options_annotation)
            ):
                return True
        return False

    if (
        isinstance(
            value,
            field.annotation.__origin__,
        )
        is False
    ):
        return False

    if issubclass(field.annotation.__origin__, dict):
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
    for item in value:
        is_valid = False
        for type_options in field.annotation.__args__:
            if _validate_field_value(
                item, FieldMeta.get_generic_field_meta(type_options)
            ):
                is_valid = True
                break
        if is_valid:
            continue
        return False
    return True


class Validator:
    """
    Validator provides a __init__ attribute type checker.
    Will rise a TypeError exception with all validation errors
    Obs: dict values are not allowed
    """

    __custom_exception__: Type[Exception] = None
    __field_map__: list[FieldMeta] = None
    __lazy_type_check__: bool = False

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

    def __post_init__(self):
        self.__validate_model()

    def __validate_model(self):
        _errors = []
        for field in self.__with_field_map():
            if (
                _validate_field_value(self.__dict__.get(field.name, _empty), field)
                is False
            ):
                _errors.append(
                    f"Wrong type for {field.name}:"
                    f" {field.annotation} != '{type(self.__dict__.get(field.name, _empty))}'"
                )
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
    def set_lazy_type_check(cls, on: bool):
        """
        Will change the type  (TypeError)
        """
        cls.__lazy_type_check__ = on

    def __repr__(self):
        class_name = self.__class__.__name__
        values = []
        for field_map in self.__with_field_map():
            attr_value = object.__getattribute__(self, field_map.name)
            values.append(f"{field_map.name}={attr_value}")
        return f"<{class_name} ({', '.join(values)})>"

    def __str__(self):
        return self.__repr__()
