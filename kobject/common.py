"""
Field definition and field map generator
"""
from dataclasses import dataclass
from inspect import _empty, Signature
from typing import Type, Any, TypeVar, List, Dict

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


class InheritanceFieldMeta:  # pylint: disable=R0903
    """
    InheritanceFieldMeta will provide a __with_field_map() to allow preload
    information for execute validation, decode and encode.
    """

    __field_map: Dict[Type, list[FieldMeta]] = {}

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
