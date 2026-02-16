import datetime
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from json import JSONDecodeError
from uuid import UUID

import pytest

from kobject import Empty, Kobject


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
    a_list_of_int: list[int]
    a_tuple_of_bool: tuple[bool]
    a_base_a: BaseA
    a_base_b: BaseB
    a_list_of_base_a: list[BaseA]
    a_int_default_none: int = None
    a_list_field: list = field(default_factory=list)


@dataclass
class BaseD(Kobject):
    a_list_of_int: list[int]
    a_list_of_bool: list[bool]
    a_list_of_float: list[float]
    a_list_of_str: list[int]


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
    error_msg = error.value.args[0]
    assert "Class 'BaseA' type error:" in error_msg
    assert "Wrong type for a_datetime:" in error_msg
    assert "datetime.datetime" in error_msg
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
    error_msg = error.value.args[0]
    assert "Missing content the follow attr are not present:" in error_msg
    assert "a_int: <class 'int'> != `Empty`" in error_msg
    assert "a_str: <class 'str'> != `Empty`" in error_msg
    assert "a_list_of_int:" in error_msg and "!= `Empty`" in error_msg
    assert "a_tuple_of_bool:" in error_msg
    assert "a_base_a:" in error_msg
    assert "a_base_b:" in error_msg
    assert "a_list_of_base_a:" in error_msg
    json_errors = error.value.json_error()
    assert len(json_errors) == 7
    assert json_errors[0] == {"field": "a_int", "type": int, "value": "Empty"}
    assert json_errors[1] == {"field": "a_str", "type": str, "value": "Empty"}
    assert json_errors[2]["field"] == "a_list_of_int"
    assert json_errors[2]["value"] == "Empty"
    assert json_errors[3]["field"] == "a_tuple_of_bool"
    assert json_errors[4]["field"] == "a_base_a"
    assert json_errors[5]["field"] == "a_base_b"
    assert json_errors[6]["field"] == "a_list_of_base_a"
    Kobject.set_content_check_custom_exception(None)


def test_from_json_empty_payload():
    Kobject.set_content_check_custom_exception(None)
    with pytest.raises(TypeError) as error:
        BaseC.from_json(payload=b"{}")
    error_msg = error.value.args[0]
    assert "Missing content the follow attr are not present:" in error_msg
    assert "a_int: <class 'int'> != `Empty`" in error_msg
    assert "a_str: <class 'str'> != `Empty`" in error_msg
    assert "a_list_of_int:" in error_msg
    assert "a_tuple_of_bool:" in error_msg
    assert "a_base_a:" in error_msg
    assert "a_base_b:" in error_msg
    assert "a_list_of_base_a:" in error_msg
    json_errors = error.value.json_error()
    assert len(json_errors) == 7
    assert json_errors[0] == {"field": "a_int", "type": int, "value": "Empty"}
    assert json_errors[1] == {"field": "a_str", "type": str, "value": "Empty"}
    assert json_errors[2]["field"] == "a_list_of_int"
    assert json_errors[3]["field"] == "a_tuple_of_bool"
    assert json_errors[4]["field"] == "a_base_a"
    assert json_errors[5]["field"] == "a_base_b"
    assert json_errors[6]["field"] == "a_list_of_base_a"


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
    error_msg = error.value.args[0]
    assert "Class 'BaseD' type error:" in error_msg
    assert "Wrong type for a_list_of_int:" in error_msg
    assert "!= `None`" in error_msg
    assert "Wrong type for a_list_of_bool:" in error_msg
    assert "!= `0`" in error_msg
    assert "Wrong type for a_list_of_float:" in error_msg
    assert "!= `'lala'`" in error_msg
    assert "Wrong type for a_list_of_str:" in error_msg
    assert "!= `1.3`" in error_msg
    json_errors = error.value.json_error()
    assert len(json_errors) == 4
    assert json_errors[0]["field"] == "a_list_of_int"
    assert json_errors[0]["value"] == "None"
    assert json_errors[1]["field"] == "a_list_of_bool"
    assert json_errors[1]["value"] == "0"
    assert json_errors[2]["field"] == "a_list_of_float"
    assert json_errors[2]["value"] == "'lala'"
    assert json_errors[3]["field"] == "a_list_of_str"
    assert json_errors[3]["value"] == "1.3"


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
    error_msg = error.value.args[0]
    assert "Class 'BaseG' type error:" in error_msg
    assert "Wrong type for a_tuple:" in error_msg
    assert "!= `None`" in error_msg
    assert "Wrong type for a_dict:" in error_msg
    json_errors = error.value.json_error()
    assert len(json_errors) == 2
    assert json_errors[0]["field"] == "a_tuple"
    assert json_errors[0]["value"] == "None"
    assert json_errors[1]["field"] == "a_dict"
    assert json_errors[1]["value"] == "None"


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
