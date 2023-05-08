import datetime
from dataclasses import dataclass, field
from enum import Enum
from json import JSONDecodeError
from typing import List, Tuple
from uuid import UUID

import pytest

from kobject import Kobject, ToJSON
from kobject.from_json import FromJSON


@dataclass
class BaseA(Kobject, FromJSON, ToJSON):
    a_datetime: datetime.datetime


@dataclass
class BaseB:
    a_uuid: UUID


@dataclass
class BaseC(Kobject, FromJSON, ToJSON):
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
class BaseD(Kobject, FromJSON, ToJSON):
    a_list_of_int: List[int]
    a_list_of_bool: List[bool]
    a_list_of_float: List[float]
    a_list_of_str: List[int]


@dataclass
class BaseE(Kobject, FromJSON, ToJSON):
    a_list_of_int: int
    a_list_of_bool: bool
    a_list_of_float: float
    a_list_of_str: int


class StubEnum(Enum):
    LORO = 1


@dataclass
class BaseF(Kobject, FromJSON, ToJSON):
    a_stub_enum: StubEnum


def test_from_json_error_default_exception():
    with pytest.raises(JSONDecodeError) as error:
        BaseC.from_json(payload=b"{")
    assert error.value.args == (
        "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
    )


def test_from_json_error_custom_exception():
    FromJSON.set_custom_exception(Exception)
    with pytest.raises(Exception) as error:
        BaseC.from_json(payload=b"{")
    assert error.value.args == ("Invalid content -> b'{'",)
    FromJSON.set_custom_exception(None)


def test_from_json():
    FromJSON.set_decoder_resolver(
        datetime.datetime,
        lambda attr_type, value: datetime.datetime.fromisoformat(value)
        if isinstance(value, str)
        else value,
    )
    FromJSON.set_decoder_resolver(
        BaseB,
        lambda attr_type, value: attr_type(a_uuid=UUID(value["a_uuid"]))
        if isinstance(value, dict)
        else value,
    )
    payload = (
        b'{"a_int": 1,"a_str": "lala","a_list_of_int": [1,2,3],'
        b'"a_tuple_of_bool": [true],"a_base_a": {"a_date'
        b'time": "2023-02-01 17:38:45.389426"},"a_base_b": {"a_'
        b'uuid":"1d9cf695-c917-49ce-854b-4063f0cda2e7"}, "a_lis'
        b't_of_base_a": [{"a_datetime": "2023-02-01 17:38:45.389426"}],'
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

    FromJSON.set_custom_exception(MyException)
    with pytest.raises(MyException) as error:
        BaseC.from_json(payload=b"{}")
    assert error.value.args == ("Invalid content -> b'{}'",)
    FromJSON.set_custom_exception(None)


def test_from_json_empty_payload():
    FromJSON.set_custom_exception(None)
    with pytest.raises(TypeError) as error:
        BaseC.from_json(payload=b"{}")
    assert error.value.args == (
        "Missing content -> The fallow attr are not presente a_int, a_str"
        ", a_list_of_int, a_tuple_of_bool, a_base_a, a_base_b, a_list_of_"
        "base_a",
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
        "Validation Errors:\n    'a_list_of_int' : Wrong type! Expected <class "
        "'list'> but giving <class 'NoneType'>\n    'a_list_of_bool' : Wrong ty"
        "pe! Expected <class 'list'> but giving <class 'int'>\n    'a_list_of_f"
        "loat' : Wrong type! Expected <class 'list'> but giving <class 'str'>\n"
        "    'a_list_of_str' : Wrong type! Expected <class 'list'> but giving <"
        "class 'float'>\n",
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
        "Validation Errors:\n    'a_list_of_int' : Wrong type! Expected <class 'int'"
        "> but giving <class 'list'>\n    'a_list_of_bool' : Wrong type! Expected <c"
        "lass 'bool'> but giving <class 'list'>\n    'a_list_of_float' : Wrong type!"
        " Expected <class 'float'> but giving <class 'list'>\n    'a_list_of_str' : "
        "Wrong type! Expected <class 'int'> but giving <class 'list'>\n",
    )


def test_from_json_error_enum_invalid_value():
    with pytest.raises(TypeError) as error:
        BaseF.from_json(payload=b'{"a_stub_enum": 2}')
    assert error.value.args == (
        "Validation Errors:\n    'a_stub_enum' : Wrong type! Expected <enum 'StubEnum'> but giving <class 'int'>\n",
    )
