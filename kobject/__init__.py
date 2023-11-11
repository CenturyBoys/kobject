"""
Know your object a __init__ type validator
"""

from kobject.from_json import FromJSON
from kobject.to_json import ToJSON
from kobject.validator import Validator


class Kobject(Validator, FromJSON, ToJSON):
    """Just use it."""


__all__ = ["Kobject", "FromJSON", "ToJSON"]
