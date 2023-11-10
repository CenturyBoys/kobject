from dataclasses import dataclass
from inspect import _empty
from typing import Type, Any, TypeVar


T = TypeVar("T")
__base_any_type__ = {}


@dataclass(slots=True, frozen=True)
class FieldMeta:
    name: str
    annotation: Type[Any]
    required: bool
    have_default_value: bool
    default: Any

    @classmethod
    def new_one(cls, name: str, annotation: Type[Any], value: Any):
        return cls(
            name=name,
            annotation=annotation,
            required=value == _empty,
            default=value,
            have_default_value=value != _empty,
        )

    @classmethod
    def any_one(cls, annotation: Type[Any]):
        return cls(
            name="",
            annotation=annotation,
            required=True,
            default=_empty,
            have_default_value=False,
        )

    @classmethod
    def get_generic_field_meta(cls, any_type: Type[Any]):
        if obj := __base_any_type__.get(any_type):
            return obj
        obj = FieldMeta.any_one(any_type)
        __base_any_type__.update({any_type: obj})
        return obj
