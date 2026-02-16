"""Core Kobject base class for runtime type validation."""

from __future__ import annotations

import json
import types
from collections.abc import Callable
from inspect import Signature
from typing import Any, ClassVar, TypeVar

from kobject.fields import FieldMeta
from kobject.schema import JSONSchemaGenerator
from kobject.serialization import (
    JSONDecoder,
    JSONEncoder,
    _checker,
    _resolve_dict,
    _resolve_list,
    _resolve_tuple,
)
from kobject.validation import _validate_field_value

T = TypeVar("T")


class Kobject:
    """
    Base class for runtime type validation.

    Validates __init__ parameter types at instantiation time.
    Supports both dataclasses and regular classes.

    Example:
        @dataclass
        class User(Kobject):
            name: str
            age: int

        user = User(name="Alice", age=30)  # OK
        user = User(name="Alice", age="30")  # Raises TypeError
    """

    __field_map: ClassVar[dict[type[Any], list[FieldMeta]]] = {}
    __custom_exception__: type[Exception] | None = None
    __lazy_type_check__: bool = False
    __from_json_custom_exception__: type[Exception] | None = None

    @classmethod
    def _with_field_map(cls) -> list[FieldMeta]:
        """
        Will process the class map field the first time and
        use pre-processed field after the first call.
        """
        if cls.__field_map.get(cls) is None:
            cls.__field_map[cls] = []
            for param in Signature.from_callable(cls).parameters.values():
                cls.__field_map[cls].append(
                    FieldMeta.new_one(
                        name=param.name,
                        annotation=param.annotation,
                        value=param.default,
                    )
                )
        return cls.__field_map[cls]

    def __post_init__(self) -> None:
        self.__validate_model()

    def __validate_model(self) -> None:
        _errors: list[dict[str, Any]] = []
        for field in self._with_field_map():
            _value = getattr(self, field.name)
            if _validate_field_value(_value, field) is False:
                _errors.append(
                    {
                        "field": field.name,
                        "type": field.annotation,
                        "value": _value.__repr__(),
                    }
                )
                assert isinstance(self.__lazy_type_check__, bool)
                if self.__lazy_type_check__:
                    break
        if _errors:
            exception = self.__custom_exception__
            if self.__custom_exception__ is None:
                exception = TypeError
            _exception = exception(
                "Class '{}' type error:\n {}".format(
                    self.__class__.__name__,
                    "\n ".join(
                        [
                            "Wrong type for {field}: {type} != `{value}`".format(**_e)
                            for _e in _errors
                        ]
                    ),
                )
            )
            raise self._enriched_error(_exception, _errors)

    @staticmethod
    def _enriched_error(
        exception: Exception, errors: list[dict[str, Any]]
    ) -> Exception:
        object.__setattr__(exception, "__structured_validation_errors__", errors)

        def json_error(self: Exception) -> list[dict[str, Any]]:
            return self.__structured_validation_errors__  # type: ignore[attr-defined]

        exception.json_error = types.MethodType(json_error, exception)  # type: ignore[attr-defined]

        return exception

    @classmethod
    def set_validation_custom_exception(cls, exception: type[Exception] | None) -> None:
        """
        Will change the default validation error (TypeError).
        """
        cls.__custom_exception__ = exception

    @classmethod
    def set_lazy_type_check(cls, status: bool) -> None:
        """
        Will change the type check behavior.
        When True, validation stops at first error.
        """
        cls.__lazy_type_check__ = status

    @classmethod
    def set_content_check_custom_exception(
        cls, exception: type[Exception] | None
    ) -> None:
        """
        Will change the default JSONDecodeError error.
        """
        cls.__from_json_custom_exception__ = exception

    @staticmethod
    def set_decoder_resolver(
        attr_type: type[Any], resolver_callback: Callable[..., Any]
    ) -> None:
        """
        Register a resolver for a class or subclass.

        attr_type: int, str, bool, float or any other class
        resolver_callback: lambda function that receives the type and value to be cast.
         Example 'lambda attr_type, value: value'
        """
        JSONDecoder.register_resolver(attr_type, resolver_callback)

    @staticmethod
    def set_encoder_resolver(
        attr_type: type[Any],
        resolver_callback: Callable[..., Any],
        on_dict: bool = True,
    ) -> None:
        """
        Register a resolver for a class or subclass.

        attr_type: int, str, bool, float or any other class
        resolver_callback: lambda function that receives the value to be cast.
        on_dict: bool if this encoder must be called on dict() function too.
         Example 'lambda value: value'
        """
        JSONEncoder.register_resolver(attr_type, resolver_callback, on_dict)

    @staticmethod
    def set_schema_resolver(
        attr_type: type[Any],
        resolver_callback: Callable[[type[Any]], dict[str, Any]],
    ) -> None:
        """
        Register a schema resolver for a class or subclass.

        attr_type: The type to match (supports subclass matching)
        resolver_callback: Function that returns JSON Schema dict for the type.
         Example 'lambda t: {"type": "string", "format": "date-time"}'
        """
        JSONSchemaGenerator.register_resolver(attr_type, resolver_callback)

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        """
        Generate JSON Schema Draft 7 for this class.

        Returns:
            Complete JSON Schema dict with $schema, properties, etc.
        """
        return JSONSchemaGenerator.generate(cls)

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        values = [
            f"{field_map.name}={getattr(self, field_map.name)}"
            for field_map in self._with_field_map()
        ]
        return f"<{class_name} ({', '.join(values)})>"

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def from_json(cls: type[T], payload: bytes) -> T:
        """
        Returns a class instance by the given JSON payload.
        """
        try:
            dict_repr = json.loads(payload)
            instance = cls.from_dict(dict_repr=dict_repr)
            return instance
        except TypeError as original_error:
            _exception: Exception = original_error
            if cls.__from_json_custom_exception__ is not None:
                _exception = cls.__from_json_custom_exception__(original_error.args[0])

            if hasattr(original_error, "json_error"):
                _exception = cls._enriched_error(
                    _exception,
                    original_error.json_error(),  # type: ignore[attr-defined]
                )

            raise _exception from None
        except Exception as original_error:
            _exception = original_error

            if cls.__from_json_custom_exception__ is not None:
                _exception = cls.__from_json_custom_exception__(
                    f"Invalid content -> {payload!s}",
                )

            _exception = cls._enriched_error(
                _exception,
                [
                    {
                        "field": cls.__name__,
                        "type": type(cls),
                        "value": str(payload),
                    }
                ],
            )

            raise _exception from original_error

    @classmethod
    def from_dict(cls: type[T], dict_repr: dict[str, Any]) -> T:
        """
        Returns a class instance by the given dict representation.
        """

        _missing: list[dict[str, Any]] = []
        _dict_repr: dict[str, Any] = {}
        for field in cls._with_field_map():
            attr_value = dict_repr.get(field.name)
            _is_missing = field.name not in dict_repr
            if _is_missing and field.have_default_value:
                continue
            if _is_missing:
                _missing.append(
                    {
                        "field": field.name,
                        "type": field.annotation,
                        "value": "Empty",
                    }
                )
                continue

            _dict_repr.update({field.name: attr_value})
            if attr_value == field.default:
                continue

            base_type = JSONDecoder.get_base_type(attr_type=field.annotation)

            if base_type is type(None) and attr_value is None:
                _dict_repr[field.name] = attr_value

            elif _checker(base_type, list | tuple | dict) is False:
                _dict_repr[field.name] = JSONDecoder.type_caster(
                    attr_type=field.annotation, attr_value=attr_value
                )

            elif _checker(base_type, list) and isinstance(attr_value, list):
                _dict_repr[field.name] = _resolve_list(
                    _type=field.annotation, attr_value=attr_value
                )

            elif _checker(base_type, tuple) and isinstance(attr_value, list):
                _dict_repr[field.name] = _resolve_tuple(
                    _type=field.annotation, attr_value=attr_value
                )

            elif _checker(base_type, dict) and isinstance(attr_value, dict):
                _dict_repr[field.name] = _resolve_dict(
                    _type=field.annotation, attr_value=attr_value
                )

        if _missing:
            _exception = TypeError(
                "Missing content the follow attr are not present:\n{}".format(
                    "\n".join(
                        ["{field}: {type} != `{value}`".format(**_e) for _e in _missing]
                    )
                )
            )

            _exception = cls._enriched_error(_exception, _missing)
            raise _exception
        return cls(**_dict_repr)

    def dict(self, remove_nones: bool = False) -> dict[str, Any]:
        """
        Returns dict representation of your object.
        """
        return self._dict(resolver=JSONEncoder.dict_default, remove_nones=remove_nones)

    def to_dict(self, remove_nones: bool = False) -> dict[str, Any]:
        """
        Returns dict representation of your object.
        """
        return self._dict(resolver=JSONEncoder.dict_default, remove_nones=remove_nones)

    def to_json(self, remove_nones: bool = False) -> bytes:
        """
        Returns JSON bytes of your object.
        """
        dict_repr = self._dict(resolver=JSONEncoder.default, remove_nones=remove_nones)
        json_bytes = json.dumps(
            dict_repr, default=JSONEncoder.default, separators=(",", ":")
        )
        return json_bytes.encode()

    def _dict(
        self, resolver: Callable[[Any], Any], remove_nones: bool = False
    ) -> dict[str, Any]:
        def resolve(obj: Any) -> Any:
            if isinstance(obj, Kobject):
                return obj.dict(remove_nones=remove_nones)
            return resolver(obj)

        _dict_representation: dict[str, Any] = {}

        for field in self._with_field_map():
            attr_value = getattr(self, field.name)

            if remove_nones and attr_value is None:
                continue

            if not isinstance(attr_value, list | tuple | dict):
                _dict_representation.update({field.name: resolve(attr_value)})
                continue
            if isinstance(attr_value, list | tuple):
                attr_value_new: list[Any] = []
                for attr_value_item in attr_value:
                    if remove_nones and attr_value_item is None:
                        continue
                    attr_value_new.append(resolve(attr_value_item))
                _dict_representation.update({field.name: attr_value_new})
            else:
                attr_value_dict: dict[Any, Any] = {}
                for key, value in attr_value.items():
                    if remove_nones and value is None:
                        continue
                    attr_value_dict.update({resolve(key): resolve(value)})
                _dict_representation.update({field.name: attr_value_dict})

        return _dict_representation
