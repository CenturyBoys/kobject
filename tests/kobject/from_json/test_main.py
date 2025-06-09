import datetime
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from json import JSONDecodeError
from typing import List, Tuple
from uuid import UUID

import pytest

from kobject import Kobject, Empty


class EnumStub(IntEnum):
    A = 1


@dataclass
class BaseA(Kobject):
    a_datetime: datetime.datetime
    a_enum: None | EnumStub = Empty


@dataclass
class BaseB:
    a_uuid: UUID


@dataclass
class BaseC(Kobject):
    a_int: int
    a_str: str
    a_list_of_int: List[int]
    a_tuple_of_bool: Tuple[bool]
    a_base_a: BaseA
    a_base_b: BaseB
    a_list_of_base_a: List[BaseA]
    a_int_default_none: int = None
    a_list_field: list = field(default_factory=list)


@dataclass
class BaseD(Kobject):
    a_list_of_int: List[int]
    a_list_of_bool: List[bool]
    a_list_of_float: List[float]
    a_list_of_str: List[int]


@dataclass
class BaseE(Kobject):
    a_list_of_int: int
    a_list_of_bool: bool
    a_list_of_float: float
    a_list_of_str: int


class StubEnum(Enum):
    LORO = 1


@dataclass
class BaseF(Kobject):
    a_stub_enum: StubEnum
    b_stub_enum: StubEnum = None


class BaseG(Kobject):
    a_tuple: tuple[int, int]
    a_dict: dict[str, BaseB]

    def __init__(self, a_tuple: tuple[int, int], a_dict: dict[str, BaseB]):
        self.a_tuple = a_tuple
        self.a_dict = a_dict
        self.__post_init__()


def test_from_json_error_default_exception():
    with pytest.raises(JSONDecodeError) as error:
        BaseC.from_json(payload=b"{")
    assert error.value.args == (
        "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
    )


def test_from_json_error_custom_exception():
    Kobject.set_content_check_custom_exception(Exception)
    with pytest.raises(Exception) as error:
        BaseC.from_json(payload=b"{")
    assert error.value.args == ("Invalid content -> b'{'",)
    Kobject.set_content_check_custom_exception(None)


def test_from_json_unable_to_cast():
    class MyException(Exception):
        pass

    Kobject.set_content_check_custom_exception(MyException)
    payload = (
        b'{"a_int": 1,"a_str": "lala","a_list_of_int": [1,2,3],'
        b'"a_tuple_of_bool": [true],"a_base_a": {"a_date'
        b'time": "2023-02-01 17:38:45.389426"},"a_base_b": {"a_'
        b'uuid":"1d9cf695-c917-49ce-854b-4063f0cda2e7"}, "a_lis'
        b't_of_base_a": [{"a_datetime": "2023-02-01 17:38:45.389426", "a_enum": 1}],'
        b' "a_int_default_none": null}'
    )
    with pytest.raises(MyException) as error:
        BaseC.from_json(payload=payload)
    assert error.value.args == (
        "Class 'BaseA' type error:\n Wrong type for a_datetime: <class 'datetime.datetime'> != '<class 'str'>'",
    )
    Kobject.set_content_check_custom_exception(Exception)


def test_from_json():
    Kobject.set_decoder_resolver(
        datetime.datetime,
        lambda attr_type, value: datetime.datetime.fromisoformat(value)
        if isinstance(value, str)
        else value,
    )
    Kobject.set_decoder_resolver(
        BaseB,
        lambda attr_type, value: attr_type(a_uuid=UUID(value["a_uuid"]))
        if isinstance(value, dict)
        else value,
    )
    Kobject.set_decoder_resolver(
        IntEnum,
        lambda attr_type, value: attr_type(value) if isinstance(value, int) else value,
    )
    payload = (
        b'{"a_int": 1,"a_str": "lala","a_list_of_int": [1,2,3],'
        b'"a_tuple_of_bool": [true],"a_base_a": {"a_date'
        b'time": "2023-02-01 17:38:45.389426"},"a_base_b": {"a_'
        b'uuid":"1d9cf695-c917-49ce-854b-4063f0cda2e7"}, "a_lis'
        b't_of_base_a": [{"a_datetime": "2023-02-01 17:38:45.389426", "a_enum": 1}],'
        b' "a_int_default_none": null}'
    )
    instance = BaseC.from_json(payload=payload)
    assert isinstance(instance, BaseC)
    assert isinstance(instance.a_base_a, BaseA)
    assert isinstance(instance.a_base_b, BaseB)
    assert isinstance(instance.a_list_of_base_a[0], BaseA)


def test_from_json_empty_payload_custom_exception():
    class MyException(Exception):
        pass

    Kobject.set_content_check_custom_exception(MyException)
    with pytest.raises(MyException) as error:
        BaseC.from_json(payload=b"{}")
    assert error.value.args == (
        "Missing content -> The fallow attr are not presente a_int, a_str, "
        "a_list_of_int, a_tuple_of_bool, a_base_a, a_base_b, a_list_of_base_a",
    )
    Kobject.set_content_check_custom_exception(None)


def test_from_json_empty_payload():
    Kobject.set_content_check_custom_exception(None)
    with pytest.raises(TypeError) as error:
        BaseC.from_json(payload=b"{}")
    assert error.value.args == (
        "Missing content -> The fallow attr are not presente a_int, a_str, "
        "a_list_of_int, a_tuple_of_bool, a_base_a, a_base_b, a_list_of_base_a",
    )


def test_from_json_wrong_type_expected_list():
    payload = (
        b"{"
        b'"a_list_of_int": null,'
        b'"a_list_of_bool": 0,'
        b'"a_list_of_float": "lala",'
        b'"a_list_of_str": 1.3'
        b"}"
    )
    with pytest.raises(TypeError) as error:
        BaseD.from_json(payload=payload)
    assert error.value.args == (
        "Class 'BaseD' type error:\n"
        " Wrong type for a_list_of_int: typing.List[int] != '<class 'NoneType'>'\n"
        " Wrong type for a_list_of_bool: typing.List[bool] != '<class 'int'>'\n"
        " Wrong type for a_list_of_float: typing.List[float] != '<class 'str'>'\n"
        " Wrong type for a_list_of_str: typing.List[int] != '<class 'float'>'",
    )


def test_from_json_wrong_type_list():
    payload = (
        b"{"
        b'"a_list_of_int": [],'
        b'"a_list_of_bool": [],'
        b'"a_list_of_float": [],'
        b'"a_list_of_str": []'
        b"}"
    )
    with pytest.raises(TypeError) as error:
        BaseE.from_json(payload=payload)
    assert error.value.args == (
        "Class 'BaseE' type error:\n"
        " Wrong type for a_list_of_int: <class 'int'> != '<class 'list'>'\n"
        " Wrong type for a_list_of_bool: <class 'bool'> != '<class 'list'>'\n"
        " Wrong type for a_list_of_float: <class 'float'> != '<class 'list'>'\n"
        " Wrong type for a_list_of_str: <class 'int'> != '<class 'list'>'",
    )


def test_from_json_error_enum_invalid_value():
    with pytest.raises(TypeError) as error:
        BaseF.from_json(payload=b'{"a_stub_enum": 2,"b_stub_enum": null}')
    assert error.value.args == (
        "Class 'BaseF' type error:\n"
        " Wrong type for a_stub_enum: <enum 'StubEnum'> != '<class 'int'>'",
    )


def test_from_json_enum_with_default_value():
    obj = BaseF.from_json(payload=b'{"a_stub_enum": 1,"b_stub_enum": 1}')
    assert obj.a_stub_enum == StubEnum.LORO
    assert obj.b_stub_enum == StubEnum.LORO


def test_from_json_enum_with_default_value_set():
    obj = BaseF.from_json(payload=b'{"a_stub_enum": 1}')
    assert obj.a_stub_enum == StubEnum.LORO
    assert obj.b_stub_enum is None


def test_from_json_tuple_invalid_value():
    with pytest.raises(TypeError) as error:
        BaseG.from_json(payload=b'{"a_tuple":null,"a_dict":null}')
    assert error.value.args == (
        "Class 'BaseG' type error:\n"
        " Wrong type for a_tuple: tuple[int, int] != '<class 'NoneType'>'\n"
        " Wrong type for a_dict: dict[str, tests.kobject.from_json.test_main.BaseB] != '<class 'NoneType'>'",
    )


def test_from_json_tuple_and_dict_cast():
    Kobject.set_decoder_resolver(
        BaseB,
        lambda attr_type, value: attr_type(a_uuid=UUID(value["a_uuid"]))
        if isinstance(value, dict)
        else value,
    )
    obj = BaseG.from_json(
        payload=b'{"a_tuple":[1,2],"a_dict":{"m":{"a_uuid":"1d9cf695-c917-49ce-854b-4063f0cda2e7"}}}'
    )
    assert obj.a_tuple == (1, 2)
    assert obj.a_dict == {
        "m": BaseB(a_uuid=UUID("1d9cf695-c917-49ce-854b-4063f0cda2e7"))
    }
