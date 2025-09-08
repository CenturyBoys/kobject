import datetime
import typing
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
        "Class 'BaseA' type error:\n Wrong type for a_datetime: <class 'datetime.datetime'> != `'2023-02-01 17:38:45.389426'`",
    )
    assert error.value.json_error() == [
        {
            "field": "a_datetime",
            "type": datetime.datetime,
            "value": "'2023-02-01 17:38:45.389426'",
        }
    ]
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
        "Missing content the fallow attr are not presente:\n"
        "a_int: <class 'int'> != `Empty`\n"
        "a_str: <class 'str'> != `Empty`\n"
        "a_list_of_int: typing.List[int] != `Empty`\n"
        "a_tuple_of_bool: typing.Tuple[bool] != `Empty`\n"
        "a_base_a: <class 'tests.kobject.from_json.test_main.BaseA'> != `Empty`\n"
        "a_base_b: <class 'tests.kobject.from_json.test_main.BaseB'> != `Empty`\n"
        "a_list_of_base_a: typing.List[tests.kobject.from_json.test_main.BaseA] != `Empty`",
    )
    assert error.value.json_error() == [
        {"field": "a_int", "type": int, "value": "Empty"},
        {"field": "a_str", "type": str, "value": "Empty"},
        {"field": "a_list_of_int", "type": typing.List[int], "value": "Empty"},
        {"field": "a_tuple_of_bool", "type": typing.Tuple[bool], "value": "Empty"},
        {"field": "a_base_a", "type": BaseA, "value": "Empty"},
        {"field": "a_base_b", "type": BaseB, "value": "Empty"},
        {"field": "a_list_of_base_a", "type": typing.List[BaseA], "value": "Empty"},
    ]
    Kobject.set_content_check_custom_exception(None)


def test_from_json_empty_payload():
    Kobject.set_content_check_custom_exception(None)
    with pytest.raises(TypeError) as error:
        BaseC.from_json(payload=b"{}")
    assert error.value.args == (
        "Missing content the fallow attr are not presente:\n"
        "a_int: <class 'int'> != `Empty`\n"
        "a_str: <class 'str'> != `Empty`\n"
        "a_list_of_int: typing.List[int] != `Empty`\n"
        "a_tuple_of_bool: typing.Tuple[bool] != `Empty`\n"
        "a_base_a: <class 'tests.kobject.from_json.test_main.BaseA'> != `Empty`\n"
        "a_base_b: <class 'tests.kobject.from_json.test_main.BaseB'> != `Empty`\n"
        "a_list_of_base_a: typing.List[tests.kobject.from_json.test_main.BaseA] != `Empty`",
    )
    assert error.value.json_error() == [
        {"field": "a_int", "type": int, "value": "Empty"},
        {"field": "a_str", "type": str, "value": "Empty"},
        {"field": "a_list_of_int", "type": typing.List[int], "value": "Empty"},
        {"field": "a_tuple_of_bool", "type": typing.Tuple[bool], "value": "Empty"},
        {"field": "a_base_a", "type": BaseA, "value": "Empty"},
        {"field": "a_base_b", "type": BaseB, "value": "Empty"},
        {"field": "a_list_of_base_a", "type": typing.List[BaseA], "value": "Empty"},
    ]


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
        " Wrong type for a_list_of_int: typing.List[int] != `None`\n"
        " Wrong type for a_list_of_bool: typing.List[bool] != `0`\n"
        " Wrong type for a_list_of_float: typing.List[float] != `'lala'`\n"
        " Wrong type for a_list_of_str: typing.List[int] != `1.3`",
    )
    assert error.value.json_error() == [
        {"field": "a_list_of_int", "type": typing.List[int], "value": "None"},
        {"field": "a_list_of_bool", "type": typing.List[bool], "value": "0"},
        {"field": "a_list_of_float", "type": typing.List[float], "value": "'lala'"},
        {"field": "a_list_of_str", "type": typing.List[int], "value": "1.3"},
    ]


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
        " Wrong type for a_list_of_int: <class 'int'> != `[]`\n"
        " Wrong type for a_list_of_bool: <class 'bool'> != `[]`\n"
        " Wrong type for a_list_of_float: <class 'float'> != `[]`\n"
        " Wrong type for a_list_of_str: <class 'int'> != `[]`",
    )
    assert error.value.json_error() == [
        {"field": "a_list_of_int", "type": int, "value": "[]"},
        {"field": "a_list_of_bool", "type": bool, "value": "[]"},
        {"field": "a_list_of_float", "type": float, "value": "[]"},
        {"field": "a_list_of_str", "type": int, "value": "[]"},
    ]


def test_from_json_error_enum_invalid_value():
    with pytest.raises(TypeError) as error:
        BaseF.from_json(payload=b'{"a_stub_enum": 2,"b_stub_enum": null}')
    assert error.value.args == (
        "Class 'BaseF' type error:\n"
        " Wrong type for a_stub_enum: <enum 'StubEnum'> != `2`",
    )
    assert error.value.json_error() == [
        {"field": "a_stub_enum", "type": StubEnum, "value": "2"}
    ]


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
        " Wrong type for a_tuple: tuple[int, int] != `None`\n"
        " Wrong type for a_dict: dict[str, tests.kobject.from_json.test_main.BaseB] != `None`",
    )
    assert error.value.json_error() == [
        {"field": "a_tuple", "type": tuple[int, int], "value": "None"},
        {"field": "a_dict", "type": dict[str, BaseB], "value": "None"},
    ]


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
