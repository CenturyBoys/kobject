"""
Know your object a __init__ type validator
"""
import json
from dataclasses import dataclass
from inspect import _empty, Signature, isclass
from types import GenericAlias
from typing import Type, Any, TypeVar, List, Dict, _GenericAlias, _SpecialForm, Callable


T = TypeVar("T")
__base_any_type__ = {}


@dataclass(slots=True, frozen=True)
class FieldMeta:
    """
    FieldMeta represent a class field and have pre-processed values to improve performance.
    """

    name: str
    annotation: Type[Any]
    required: bool
    have_default_value: bool
    default: Any

    @classmethod
    def new_one(cls, name: str, annotation: Type[Any], value: Any):
        """
        Return a new instance type and his pre-processed values
        """
        return cls(
            name=name,
            annotation=annotation,
            required=value == _empty,
            default=value,
            have_default_value=value != _empty,
        )

    @classmethod
    def _any_one(cls, annotation: Type[Any]):
        return cls(
            name="",
            annotation=annotation,
            required=True,
            default=_empty,
            have_default_value=False,
        )

    @classmethod
    def get_generic_field_meta(cls, any_type: Type[Any]):
        """
        Return a generic type, this must be used only on subtype validation.
        """
        if obj := __base_any_type__.get(any_type):
            return obj
        obj = FieldMeta._any_one(any_type)
        __base_any_type__.update({any_type: obj})
        return obj


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


def _resolve_list(_type: Type, attr_value: Any) -> list:
    attr_value_new = []
    for attr_value_item in attr_value:
        for sub_types in _type.__args__:
            try:
                attr_value_new.append(
                    JSONDecoder.type_caster(
                        attr_type=sub_types,
                        attr_value=attr_value_item,
                    )
                )
                break
            finally:
                continue
    return attr_value_new


def _resolve_tuple(_type: Type, attr_value: Any):
    attr_value_new = []
    for attr_value_item, attr_type in zip(attr_value, _type.__args__):
        attr_value_new.append(
            JSONDecoder.type_caster(
                attr_type=attr_type,
                attr_value=attr_value_item,
            )
        )
    return tuple(attr_value_new)


def _resolve_dict(_type: Type, attr_value: Any):
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


class Kobject:
    """Just use it."""

    __field_map: Dict[Type, list[FieldMeta]] = {}
    __custom_exception__: Type[Exception] = None
    __lazy_type_check__: bool = False
    __from_json_custom_exception__: Type[Exception] = None

    @classmethod
    def _with_field_map(cls) -> List[FieldMeta]:
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

    @classmethod
    def set_content_check_custom_exception(cls, exception: Type[Exception]):
        """
        Will change de default JSONDecodeError error
        """
        cls.__from_json_custom_exception__ = exception

    @staticmethod
    def set_decoder_resolver(attr_type: Type[Any], resolver_callback: Callable):
        """
        Register a resolver for a class or subclass\n

        attr_type: int,str,bool,float or any other class\n
        resolver_callback: lambda function that receives the type and value to be cast.
         Example 'lambda attr_type, value: value'
        """
        JSONDecoder.types_resolver.insert(0, (attr_type, resolver_callback))

    @staticmethod
    def set_encoder_resolver(attr_type, resolver_callback: Callable):
        """
        Register a resolver for a class or subclass
        attr_type: int,str,bool,float or any other class
        resolver_callback: lambda function that receives the value to be cast.
         Example 'lambda value: value'
        """
        JSONEncoder.base_types_resolver.update({attr_type: resolver_callback})

    def __repr__(self):
        class_name = self.__class__.__name__
        values = [
            f"{field_map.name}={getattr(self, field_map.name)}"
            for field_map in self._with_field_map()
        ]
        return f"<{class_name} ({', '.join(values)})>"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_json(cls: T, payload: bytes) -> Type[T]:
        """
        Returns a class instance by the giving json payload
        """
        try:
            dict_repr = json.loads(payload)
            instance = cls.from_dict(dict_repr=dict_repr)
            return instance
        except TypeError as original_error:
            if cls.__from_json_custom_exception__ is not None:
                raise cls.__from_json_custom_exception__(original_error.args[0])
            raise original_error
        except Exception as original_error:
            if cls.__from_json_custom_exception__ is not None:
                raise cls.__from_json_custom_exception__(  # pylint: disable=E1102
                    f"Invalid content -> {str(payload)}",
                ) from original_error
            raise original_error

    @classmethod
    def from_dict(cls: T, dict_repr: Dict) -> Type[T]:  # pylint: disable=R0914
        """
        Returns a class instance by the giving dict representation
        """

        _missing = []

        for field in cls._with_field_map():
            attr_value = dict_repr.get(field.name)
            _is_missing = field.name not in dict_repr
            if _is_missing and field.have_default_value:
                continue
            if _is_missing:
                _missing.append(field.name)
                continue

            if attr_value == field.default:
                continue

            base_type = JSONDecoder.get_base_type(attr_type=field.annotation)

            if issubclass(base_type, list | tuple | dict) is False:
                dict_repr[field.name] = JSONDecoder.type_caster(
                    attr_type=field.annotation, attr_value=attr_value
                )

            elif issubclass(base_type, list) and isinstance(attr_value, list):
                dict_repr[field.name] = _resolve_list(
                    _type=field.annotation, attr_value=attr_value
                )

            elif issubclass(base_type, tuple) and isinstance(attr_value, list):
                dict_repr[field.name] = _resolve_tuple(
                    _type=field.annotation, attr_value=attr_value
                )

            elif issubclass(base_type, dict) and isinstance(attr_value, dict):
                dict_repr[field.name] = _resolve_dict(
                    _type=field.annotation, attr_value=attr_value
                )

        if _missing:
            raise TypeError(
                f"Missing content -> The fallow attr are not presente {', '.join(_missing)}"
            )
        return cls(**dict_repr)

    def dict(self):
        """
        Returns dict representation of your object
        """
        _dict_representation = {}

        for field in self._with_field_map():
            attr_value = getattr(self, field.name)
            if not isinstance(attr_value, list | tuple | dict):
                _dict_representation.update(
                    {field.name: JSONEncoder.default(attr_value)}
                )
                continue
            if isinstance(attr_value, list | tuple):
                attr_value_new = []
                for attr_value_item in attr_value:
                    attr_value_new.append(JSONEncoder.default(attr_value_item))
                _dict_representation.update({field.name: attr_value_new})
            else:
                attr_value_new = {}
                for key, value in attr_value.items():
                    attr_value_new.update(
                        {JSONEncoder.default(key): JSONEncoder.default(value)}
                    )
                _dict_representation.update({field.name: attr_value_new})

        return _dict_representation

    def to_json(self) -> bytes:
        """
        Returns json of your object
        """
        dict_repr = self.dict()
        json_bytes = json.dumps(
            dict_repr, default=JSONEncoder.default, separators=(",", ":")
        )
        return json_bytes.encode()


class JSONDecoder:
    """
    Implementation tyo decode json in to class instance inspired by json.JSONEncoder
    """

    types_resolver = []

    @staticmethod
    def get_base_type(attr_type):
        """
        Returns the base type if the parameter attr_type has __original__ attribute
        """
        if hasattr(attr_type, "__origin__"):
            attr_type = attr_type.__origin__
        return attr_type

    @classmethod
    def type_caster(cls, attr_type, attr_value):  # pylint: disable=R1710
        """
        Returns the result of cast attribute type for the attribute type
        """
        for map_attr_type, resolver in cls.types_resolver:
            if isclass(attr_type) and issubclass(attr_type, map_attr_type):
                return resolver(attr_type, attr_value)
        return attr_value


class JSONEncoder(json.JSONEncoder):
    """
    Self implementation for default json.JSONEncoder
    """

    base_types_resolver = {}

    @staticmethod
    def get_type(attr_type):
        """
        Returns the type or subtypes of giving attribute type
        """
        attr_type = attr_type.__origin__
        return attr_type

    @classmethod
    def default(cls, obj):  # pylint: disable=W0221
        if isinstance(obj, Kobject):
            return obj.dict()
        for map_attr_type, resolver in cls.base_types_resolver.items():
            if isinstance(obj, map_attr_type):
                return resolver(obj)
        return obj
