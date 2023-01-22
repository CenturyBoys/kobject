"""
Know your object a __init__ type validator
"""

import inspect
from typing import Union, Optional, Coroutine, Callable, Dict, Type


class Kobject:
    """
    Kobject provides a __init__ attribute type checker.
    Will rise a TypeError exception with all validation errors
    Obs: dict values are not allowed
    """

    __custom_exception: Type[Exception] = None

    @classmethod
    def set_custom_exception(cls, exception: Type[Exception]):
        """
        Will change de default validation error (TypeError)
        """
        cls.__custom_exception = exception

    def __get_attribute_metadata(self) -> dict:
        _default_values = dict(inspect.signature(self.__init__).parameters.items())
        return _default_values

    def __get_sub_attribute_type(self, attr: str):
        attr_metadata = self.__get_attribute_metadata().get(attr)
        attr_type = attr_metadata.annotation.__args__
        return attr_type

    def __get_attribute_type(self, attr: str):
        attr_metadata = self.__get_attribute_metadata().get(attr)
        attr_type = attr_metadata.annotation
        is_a_wrap_type = hasattr(attr_type, "__origin__")
        if is_a_wrap_type:
            attr_type = attr_type.__origin__
        is_not_a_real_type = attr_type.__class__ in (
            Union.__class__,
            Optional.__class__,
        )
        if is_not_a_real_type:
            attr_type = self.__get_sub_attribute_type(attr)

        return attr_type

    def __attribute_has_default_value(self, attr: str, attr_value: any) -> bool:
        attr_metadata = self.__get_attribute_metadata()
        default_value = attr_metadata.get(attr).default
        return attr_value == default_value

    def __post_init__(self):
        _errors = {}
        for attr in self.__get_attribute_metadata().keys():
            attr_value = object.__getattribute__(self, attr)
            attr_type = self.__get_attribute_type(attr=attr)
            self.__check_and_update_error_list(
                attr_value=attr_value, attr_type=attr_type, _errors=_errors, attr=attr
            )
            need_valida_content_type = isinstance(attr_value, (list, tuple))
            if need_valida_content_type:
                for index, attr_value_item in enumerate(attr_value):
                    content_types = self.__get_sub_attribute_type(attr=attr)
                    self.__check_and_update_error_list(
                        attr_value=attr_value_item,
                        attr_type=content_types,
                        _errors=_errors,
                        attr=attr,
                        index=index,
                    )
        need_raise_error = bool(_errors)
        if need_raise_error:
            message = self.__format_errors(_errors=_errors)
            exception = self.__custom_exception
            if self.__custom_exception is None:
                exception = TypeError
            raise exception(message)

    @staticmethod
    def __format_errors(_errors: dict) -> str:
        _errors_string = ["Validation Errors:\n"]
        for name, errors in _errors.items():
            _errors_string += [f"    '{name}' : {error}\n" for error in errors]
        return "".join(_errors_string)

    @staticmethod
    def __save_errors(_errors: dict, message: str, attr: any):
        if attr not in _errors:
            _errors.update({attr: []})
        _errors[attr].append(message)

    def __check_and_update_error_list(
        self,
        attr_value: any,
        attr_type: any,
        _errors: dict,
        attr: any,
        index: int = None,
    ):
        is_a_dict = attr_type in (dict, Dict)
        has_dict_on_types = isinstance(attr_type, (tuple, list)) and (
            dict in attr_type or Dict in attr_type
        )
        if is_a_dict or has_dict_on_types:
            message = f"Invalid type! The attribute '{attr}' is a {dict}"
            self.__save_errors(_errors=_errors, message=message, attr=attr)
            return

        if self.__attribute_has_default_value(attr=attr, attr_value=attr_value):
            return

        expected_callback = attr_type == Callable and not inspect.isfunction(attr_value)
        expected_coroutine = attr_type == Coroutine and not inspect.iscoroutine(
            attr_value
        )
        expected_type = not isinstance(attr_value, attr_type)
        has_type_error = expected_callback or expected_coroutine or expected_type
        if has_type_error:
            message = f"Wrong type! Expected {attr_type} but giving {type(attr_value)}"
            if index is not None:
                message += f" on index {index}"
            self.__save_errors(_errors=_errors, message=message, attr=attr)

    def __repr__(self):
        class_name = self.__class__.__name__
        values = []
        for attr in self.__get_attribute_metadata().keys():
            attr_value = object.__getattribute__(self, attr)
            values.append(f"{attr}={attr_value}")
        return f"<{class_name} ({', '.join(values)})>"
