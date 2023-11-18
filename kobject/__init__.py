"""
Know your object a __init__ type validator
"""
from enum import Enum

from kobject.validator import Kobject

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
    if any(value.__eq__(i.value) for i in attr_type)  # pylint: disable=C2801
    else value,
)

__all__ = ["Kobject"]
