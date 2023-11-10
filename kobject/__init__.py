from kobject.from_json import FromJSON
from kobject.to_json import ToJSON
from kobject.validator import Validator


class Kobject(Validator, FromJSON, ToJSON):
    pass


__all__ = ["Kobject", "FromJSON", "ToJSON"]
