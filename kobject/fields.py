"""Field metadata for Kobject validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kobject._compat import EMPTY

__base_any_type__: dict[type[Any], FieldMeta] = {}


@dataclass(slots=True, frozen=True)
class FieldMeta:
    """
    FieldMeta represents a class field with pre-processed values to improve performance.
    """

    name: str
    annotation: type[Any]
    required: bool
    have_default_value: bool
    default: Any

    @classmethod
    def new_one(cls, name: str, annotation: type[Any], value: Any) -> FieldMeta:
        """
        Return a new instance type and its pre-processed values.
        """
        return cls(
            name=name,
            annotation=annotation,
            required=value is EMPTY,
            default=value,
            have_default_value=value is not EMPTY,
        )

    @classmethod
    def _any_one(cls, annotation: type[Any]) -> FieldMeta:
        return cls(
            name="",
            annotation=annotation,
            required=True,
            default=EMPTY,
            have_default_value=False,
        )

    @classmethod
    def get_generic_field_meta(cls, any_type: type[Any]) -> FieldMeta:
        """
        Return a generic type, this must be used only on subtype validation.
        """
        if obj := __base_any_type__.get(any_type):
            return obj
        obj = FieldMeta._any_one(any_type)
        __base_any_type__.update({any_type: obj})
        return obj
