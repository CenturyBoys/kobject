"""
Know your object - a __init__ type validator.
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from uuid import UUID

from kobject.core import Kobject
from kobject.schema import JSONSchemaGenerator


class EmptyType:
    def __repr__(self) -> str:
        return "<EMPTY>"

    def __bool__(self) -> bool:
        return False


Empty = EmptyType()

# Register default resolvers for primitive types
Kobject.set_decoder_resolver(bool, lambda attr_type, value: value)
Kobject.set_decoder_resolver(
    float, lambda attr_type, value: float(value) if isinstance(value, int) else value
)
Kobject.set_decoder_resolver(int, lambda attr_type, value: value)
Kobject.set_decoder_resolver(str, lambda attr_type, value: value)
Kobject.set_decoder_resolver(
    Kobject,
    lambda attr_type, value: attr_type.from_dict(value)
    if isinstance(value, dict)
    else value,
)
Kobject.set_decoder_resolver(
    Enum,
    lambda attr_type, value: attr_type(value)
    if any(value.__eq__(i.value) for i in attr_type)
    else value,
)

# Register default schema resolvers for common types
JSONSchemaGenerator.register_resolver(
    datetime, lambda t: {"type": "string", "format": "date-time"}
)
JSONSchemaGenerator.register_resolver(
    date, lambda t: {"type": "string", "format": "date"}
)
JSONSchemaGenerator.register_resolver(
    time, lambda t: {"type": "string", "format": "time"}
)
JSONSchemaGenerator.register_resolver(
    UUID, lambda t: {"type": "string", "format": "uuid"}
)
JSONSchemaGenerator.register_resolver(
    Decimal, lambda t: {"type": "string", "pattern": r"^-?\d+(\.\d+)?$"}
)

__all__ = ["Empty", "JSONSchemaGenerator", "Kobject"]
