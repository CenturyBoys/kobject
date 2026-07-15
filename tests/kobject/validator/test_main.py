from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Generic, Literal, TypeVar

import pytest

from kobject import Empty, Kobject

_T = TypeVar("_T")


@dataclass
class Box(Kobject, Generic[_T]):
    value: _T


@dataclass
class BoxHolder(Kobject):
    box: Box[int]


class ClassType(IntEnum):
    DATACLASS = 0
    DEFAULT = 1


class StubInstance:
    def __init__(self, a_int: int):
        self.a_int = a_int


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def simple_attr(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubClass(Kobject):
            a_int: int
            a_bool: bool
            a_str: str
            a_float: float
            a_dict: dict
            a_any: Any
            a_object: StubInstance

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_int: int
            a_bool: bool
            a_str: str
            a_float: float
            a_dict: dict
            a_any: Any
            a_object: StubInstance

            def __init__(
                self,
                a_int: int,
                a_bool: bool,
                a_str: str,
                a_float: float,
                a_dict: dict,
                a_any: Any,
                a_object: StubInstance,
            ):
                self.a_int = a_int
                self.a_bool = a_bool
                self.a_str = a_str
                self.a_float = a_float
                self.a_dict = a_dict
                self.a_any = a_any
                self.a_object = a_object
                self.__post_init__()

        return StubClass


def test_simple_attr_error(simple_attr):
    with pytest.raises(TypeError) as error:

        class E:
            def __repr__(self):
                return "<E >"

        a_int = ""
        a_bool = 2
        a_str = 1.0
        a_float = True
        a_dict = True
        a_object = E()
        a_any = any([True, False, "", 1, 0.5])
        simple_attr(
            a_int=a_int,
            a_bool=a_bool,
            a_str=a_str,
            a_float=a_float,
            a_dict=a_dict,
            a_any=a_any,
            a_object=a_object,
        )
    assert error.type is TypeError
    error_msg = error.value.args[0]
    assert "Class 'StubClass' type error:" in error_msg
    assert "Wrong type for a_int: <class 'int'> != `''`" in error_msg
    assert "Wrong type for a_bool: <class 'bool'> != `2`" in error_msg
    assert "Wrong type for a_str: <class 'str'> != `1.0`" in error_msg
    assert "Wrong type for a_float: <class 'float'> != `True`" in error_msg
    assert "Wrong type for a_dict: <class 'dict'> != `True`" in error_msg
    assert "Wrong type for a_object:" in error_msg
    assert "StubInstance" in error_msg


def test_simple_attr(simple_attr):
    a_int = 1
    a_bool = True
    a_str = "a"
    a_float = 1.0
    a_dict = {}
    a_any = any([True, False, "", 1, 0.5])
    a_object = StubInstance(a_int=1)
    instance = simple_attr(
        a_int=a_int,
        a_bool=a_bool,
        a_str=a_str,
        a_float=a_float,
        a_dict=a_dict,
        a_any=a_any,
        a_object=a_object,
    )
    assert instance.a_int == a_int
    assert instance.a_bool == a_bool
    assert instance.a_str == a_str
    assert instance.a_float == a_float
    assert instance.a_dict == a_dict
    assert instance.a_any == a_any
    assert instance.a_object == a_object


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def attr_with_content(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubClass(Kobject):
            a_list_int: list[int]
            a_tuple_exactly_one_float: tuple[float]
            a_tuple_exactly_two_floats: tuple[float, float]
            a_tuple_exactly_three_floats: tuple[float, float, float]
            a_tuple_object: tuple[StubInstance]
            a_dict_str_optional_int: dict[str, None | int]
            b_dict_str_optional_int: dict[str, None | int]

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_list_int: list[int]
            a_tuple_exactly_one_float: tuple[float]
            a_tuple_exactly_two_floats: tuple[float, float]
            a_tuple_exactly_three_floats: tuple[float, float, float]
            a_tuple_object: tuple[StubInstance]
            a_dict_str_optional_int: dict[str, None | int]
            b_dict_str_optional_int: dict[str, None | int]

            def __init__(
                self,
                a_list_int: list[int],
                a_tuple_exactly_one_float: tuple[float],
                a_tuple_exactly_two_floats: tuple[float, float],
                a_tuple_exactly_three_floats: tuple[float, float, float],
                a_tuple_object: tuple[StubInstance],
                a_dict_str_optional_int: dict[str, None | int],
                b_dict_str_optional_int: dict[str, None | int],
            ):
                self.a_list_int = a_list_int
                self.a_tuple_exactly_one_float = a_tuple_exactly_one_float
                self.a_tuple_exactly_two_floats = a_tuple_exactly_two_floats
                self.a_tuple_exactly_three_floats = a_tuple_exactly_three_floats
                self.a_tuple_object = a_tuple_object
                self.a_dict_str_optional_int = a_dict_str_optional_int
                self.b_dict_str_optional_int = b_dict_str_optional_int
                self.__post_init__()

        return StubClass


def test_attr_with_content_error(attr_with_content):
    with pytest.raises(TypeError) as error:

        class E:
            def __repr__(self):
                return "<E >"

        a_list_int = [1, 2, "", 3, ""]
        a_tuple_exactly_two_floats = (1.0, "")
        a_tuple_exactly_one_float = (1.0, 1.0)
        a_tuple_exactly_three_floats = (1.0, 1.0)
        a_object = E()
        a_tuple_object = (a_object,)
        a_dict_str_optional_int = {"str": True, 1: "str", 2: True}
        b_dict_str_optional_int = {"str": True, 1: "str", 2: True}
        attr_with_content(
            a_list_int=a_list_int,
            a_tuple_exactly_one_float=a_tuple_exactly_one_float,
            a_tuple_exactly_two_floats=a_tuple_exactly_two_floats,
            a_tuple_exactly_three_floats=a_tuple_exactly_three_floats,
            a_tuple_object=a_tuple_object,
            a_dict_str_optional_int=a_dict_str_optional_int,
            b_dict_str_optional_int=b_dict_str_optional_int,
        )
    assert error.type is TypeError

    error_msg = error.value.args[0]
    assert "Class 'StubClass' type error:" in error_msg
    assert "Wrong type for a_list_int:" in error_msg
    assert "[1, 2, '', 3, '']" in error_msg
    assert "Wrong type for a_tuple_exactly_one_float:" in error_msg
    assert "(1.0, 1.0)" in error_msg
    assert "Wrong type for a_tuple_exactly_two_floats:" in error_msg
    assert "(1.0, '')" in error_msg
    assert "Wrong type for a_tuple_exactly_three_floats:" in error_msg
    assert "Wrong type for a_tuple_object:" in error_msg
    assert "(<E >,)" in error_msg
    assert "Wrong type for a_dict_str_optional_int:" in error_msg
    assert "Wrong type for b_dict_str_optional_int:" in error_msg

    json_errors = error.value.json_error()
    assert len(json_errors) == 7
    assert json_errors[0]["field"] == "a_list_int"
    assert json_errors[0]["value"] == "[1, 2, '', 3, '']"
    assert json_errors[1]["field"] == "a_tuple_exactly_one_float"
    assert json_errors[1]["value"] == "(1.0, 1.0)"
    assert json_errors[2]["field"] == "a_tuple_exactly_two_floats"
    assert json_errors[2]["value"] == "(1.0, '')"
    assert json_errors[3]["field"] == "a_tuple_exactly_three_floats"
    assert json_errors[3]["value"] == "(1.0, 1.0)"
    assert json_errors[4]["field"] == "a_tuple_object"
    assert json_errors[4]["value"] == "(<E >,)"
    assert json_errors[5]["field"] == "a_dict_str_optional_int"
    assert json_errors[6]["field"] == "b_dict_str_optional_int"


def test_attr_with_content(attr_with_content):
    a_list_int = [1, 2, 4, 3, 5]
    a_tuple_exactly_one_float = (1.0,)
    a_tuple_exactly_two_floats = (1.0, 2.0)
    a_tuple_exactly_three_floats = (1.0, 2.0, 3.0)
    a_object = StubInstance(a_int=1)
    a_tuple_object = (a_object,)
    a_dict_str_optional_int = {"str": 2}
    b_dict_str_optional_int = {"str": 2}

    instance = attr_with_content(
        a_list_int=a_list_int,
        a_tuple_exactly_one_float=a_tuple_exactly_one_float,
        a_tuple_exactly_two_floats=a_tuple_exactly_two_floats,
        a_tuple_exactly_three_floats=a_tuple_exactly_three_floats,
        a_tuple_object=a_tuple_object,
        a_dict_str_optional_int=a_dict_str_optional_int,
        b_dict_str_optional_int=b_dict_str_optional_int,
    )
    assert instance.a_list_int == a_list_int
    assert instance.a_tuple_object == a_tuple_object


class EnumStub(IntEnum):
    A = 1


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def not_real_type_attr(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubClass(Kobject):
            a_union_int_bool: int | bool
            a_optional_str: str | None
            a_optional_int: int | None
            b_optional_int: EnumStub | None = Empty

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_union_int_bool: int | bool
            a_optional_str: str | None
            a_optional_int: int | None
            b_optional_int: EnumStub | None = Empty

            def __init__(
                self,
                a_union_int_bool: int | bool,
                a_optional_str: str | None,
                a_optional_int: int | None,
                b_optional_int: EnumStub | None = Empty,
            ):
                self.a_union_int_bool = a_union_int_bool
                self.a_optional_str = a_optional_str
                self.a_optional_int = a_optional_int
                self.b_optional_int = b_optional_int
                self.__post_init__()

        return StubClass


def test_not_real_type_attr_content_error(not_real_type_attr):
    with pytest.raises(TypeError) as error:
        a_union_int_bool = "a_str"
        a_optional_str = 1
        a_optional_int = "lala"
        b_optional_int = "lala"
        not_real_type_attr(
            a_union_int_bool=a_union_int_bool,
            a_optional_str=a_optional_str,
            a_optional_int=a_optional_int,
            b_optional_int=b_optional_int,
        )
    assert error.type is TypeError

    error_msg = error.value.args[0]
    assert "Class 'StubClass' type error:" in error_msg
    assert "Wrong type for a_union_int_bool:" in error_msg
    assert "'a_str'" in error_msg
    assert "Wrong type for a_optional_str:" in error_msg
    assert "Wrong type for a_optional_int:" in error_msg
    assert "Wrong type for b_optional_int:" in error_msg

    json_errors = error.value.json_error()
    assert len(json_errors) == 4
    assert json_errors[0]["field"] == "a_union_int_bool"
    assert json_errors[0]["value"] == "'a_str'"
    assert json_errors[1]["field"] == "a_optional_str"
    assert json_errors[1]["value"] == "1"
    assert json_errors[2]["field"] == "a_optional_int"
    assert json_errors[2]["value"] == "'lala'"
    assert json_errors[3]["field"] == "b_optional_int"
    assert json_errors[3]["value"] == "'lala'"


def test_not_real_type_attr_content_set_1(not_real_type_attr):
    a_union_int_bool = 2
    a_optional_str = None
    a_optional_int = None
    b_optional_int = None
    instance = not_real_type_attr(
        a_union_int_bool=a_union_int_bool,
        a_optional_str=a_optional_str,
        a_optional_int=a_optional_int,
        b_optional_int=b_optional_int,
    )
    assert instance.a_union_int_bool == a_union_int_bool
    assert instance.a_optional_str == a_optional_str


def test_not_real_type_attr_content_set_2(not_real_type_attr):
    a_union_int_bool = True
    a_optional_str = "a_str"
    a_optional_int = 1
    b_optional_int = EnumStub.A
    instance = not_real_type_attr(
        a_union_int_bool=a_union_int_bool,
        a_optional_str=a_optional_str,
        a_optional_int=a_optional_int,
        b_optional_int=b_optional_int,
    )
    assert instance.a_union_int_bool == a_union_int_bool
    assert instance.a_optional_str == a_optional_str


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def callables_attr(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubClass(Kobject):
            a_coroutine: Coroutine
            a_callable: Callable
            b_callable: Callable

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_coroutine: Coroutine
            a_callable: Callable
            b_callable: Callable

            def __init__(
                self, a_coroutine: Coroutine, a_callable: Callable, b_callable: Callable
            ):
                self.a_coroutine = a_coroutine
                self.a_callable = a_callable
                self.b_callable = b_callable
                self.__post_init__()

        return StubClass


def test_callables_attr_content_error(callables_attr):
    with pytest.raises(TypeError) as error:
        callables_attr(
            a_coroutine=1,
            a_callable=1,
            b_callable=1,
        )
    assert error.type is TypeError
    error_msg = error.value.args[0]
    assert "Class 'StubClass' type error:" in error_msg
    assert "Wrong type for a_coroutine:" in error_msg
    assert "!= `1`" in error_msg
    assert "Wrong type for a_callable:" in error_msg
    assert "Wrong type for b_callable:" in error_msg
    json_errors = error.value.json_error()
    assert len(json_errors) == 3
    assert json_errors[0]["field"] == "a_coroutine"
    assert json_errors[0]["value"] == "1"
    assert json_errors[1]["field"] == "a_callable"
    assert json_errors[1]["value"] == "1"
    assert json_errors[2]["field"] == "b_callable"
    assert json_errors[2]["value"] == "1"


def test_callables_attr_content(callables_attr):
    import asyncio

    async def async_function():
        pass

    def function():
        pass

    a_coroutine = async_function()
    a_callable = async_function
    b_callable = function

    instance = callables_attr(
        a_coroutine=a_coroutine,
        a_callable=a_callable,
        b_callable=b_callable,
    )
    assert instance.a_coroutine == a_coroutine
    assert instance.a_callable == a_callable
    assert instance.b_callable == b_callable
    asyncio.run(a_coroutine)


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def inception_attr(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubClass(Kobject):
            a_list_union_bool_str: list[bool | str]
            a_list_optional_int: list[int | None]

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_list_union_bool_str: list[bool | str]
            a_list_optional_int: list[int | None]

            def __init__(
                self,
                a_list_union_bool_str: list[bool | str],
                a_list_optional_int: list[int | None],
            ):
                self.a_list_union_bool_str = a_list_union_bool_str
                self.a_list_optional_int = a_list_optional_int
                self.__post_init__()

        return StubClass


def test_inception_attr_content(inception_attr):
    a_list_union_bool_str = [True, ""]
    a_list_optional_int = [None, 1]
    instance = inception_attr(
        a_list_union_bool_str=a_list_union_bool_str,
        a_list_optional_int=a_list_optional_int,
    )
    assert instance.a_list_union_bool_str == a_list_union_bool_str
    assert instance.a_list_optional_int == a_list_optional_int


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def default_attr(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubClass(Kobject):
            a_bool: bool = 2

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_bool: bool = 2

            def __init__(self, a_bool: bool = 2):
                self.a_bool = a_bool
                self.__post_init__()

        return StubClass


def test_default_value_attr_error(default_attr):
    with pytest.raises(TypeError) as error:
        default_attr(a_bool="")
    assert error.type is TypeError
    assert error.value.args == (
        "Class 'StubClass' type error:\n Wrong type for a_bool: <class 'bool'> != `''`",
    )
    assert error.value.json_error() == [
        {"field": "a_bool", "type": bool, "value": "''"}
    ]


def test_default_value_attr(default_attr):
    instance = default_attr()
    assert instance.a_bool == 2


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def custom_exception(request):
    Kobject.set_validation_custom_exception(None)
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubClass(Kobject):
            a_bool: bool

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_bool: bool

            def __init__(self, a_bool: bool):
                self.a_bool = a_bool
                self.__post_init__()

        return StubClass


def test_custom_exception(custom_exception):
    class CustomException(Exception):
        pass

    with pytest.raises(TypeError) as t_error:
        custom_exception(a_bool="")
    Kobject.set_validation_custom_exception(CustomException)
    with pytest.raises(CustomException) as c_error:
        custom_exception(a_bool="")
    assert t_error.value.args == (
        "Class 'StubClass' type error:\n Wrong type for a_bool: <class 'bool'> != `''`",
    )
    assert t_error.value.json_error() == [
        {"field": "a_bool", "type": bool, "value": "''"}
    ]

    assert c_error.value.args == (
        "Class 'StubClass' type error:\n Wrong type for a_bool: <class 'bool'> != `''`",
    )
    assert c_error.value.json_error() == [
        {"field": "a_bool", "type": bool, "value": "''"}
    ]


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def lazy_validator(request):
    Kobject.set_validation_custom_exception(None)
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubClass(Kobject):
            a_bool: bool
            b_bool: bool

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_bool: bool
            b_bool: bool

            def __init__(self, a_bool: bool, b_bool: bool):
                self.a_bool = a_bool
                self.b_bool = b_bool
                self.__post_init__()

        return StubClass


def test_lazy_validator_on(lazy_validator):
    Kobject.set_lazy_type_check(True)
    with pytest.raises(TypeError) as t_error:
        lazy_validator(a_bool="", b_bool="")
    assert t_error.value.args == (
        "Class 'StubClass' type error:\n Wrong type for a_bool: <class 'bool'> != `''`",
    )
    assert t_error.value.json_error() == [
        {"field": "a_bool", "type": bool, "value": "''"}
    ]


def test_lazy_validator_off(lazy_validator):
    Kobject.set_lazy_type_check(False)
    with pytest.raises(TypeError) as t_error:
        lazy_validator(a_bool="", b_bool="")
    assert t_error.value.args == (
        "Class 'StubClass' type error:\n"
        " Wrong type for a_bool: <class 'bool'> != `''`\n"
        " Wrong type for b_bool: <class 'bool'> != `''`",
    )

    assert t_error.value.json_error() == [
        {"field": "a_bool", "type": bool, "value": "''"},
        {"field": "b_bool", "type": bool, "value": "''"},
    ]


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def literal_attr(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubClass(Kobject):
            mode: Literal["a", "b"]

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            mode: Literal["a", "b"]

            def __init__(self, mode: Literal["a", "b"]):
                self.mode = mode
                self.__post_init__()

        return StubClass


def test_literal_valid(literal_attr):
    assert literal_attr(mode="a").mode == "a"
    assert literal_attr(mode="b").mode == "b"


def test_literal_out_of_set(literal_attr):
    with pytest.raises(TypeError) as error:
        literal_attr(mode="x")
    assert "Wrong type for mode:" in error.value.args[0]


def test_literal_wrong_type(literal_attr):
    with pytest.raises(TypeError) as error:
        literal_attr(mode=1)
    assert "Wrong type for mode:" in error.value.args[0]


def test_literal_int_rejects_bool():
    @dataclass
    class StubClass(Kobject):
        flag: Literal[1, 2]

    assert StubClass(flag=1).flag == 1
    with pytest.raises(TypeError):
        StubClass(flag=True)


def test_literal_bool_rejects_int():
    @dataclass
    class StubClass(Kobject):
        flag: Literal[True]

    assert StubClass(flag=True).flag is True
    with pytest.raises(TypeError):
        StubClass(flag=1)


def test_literal_in_list():
    @dataclass
    class StubClass(Kobject):
        modes: list[Literal["a", "b"]]

    assert StubClass(modes=["a", "b", "a"]).modes == ["a", "b", "a"]
    with pytest.raises(TypeError):
        StubClass(modes=["a", "x"])


def test_literal_in_union():
    @dataclass
    class StubClass(Kobject):
        value: Literal["a", "b"] | int

    assert StubClass(value="a").value == "a"
    assert StubClass(value=10).value == 10
    with pytest.raises(TypeError):
        StubClass(value="x")


def test_generic_unbound_typevar_accepts_anything():
    # A generic model used without a binding treats its TypeVar field as Any.
    assert Box(value=5).value == 5
    assert Box(value="x").value == "x"
    assert Box(value=[1, 2]).value == [1, 2]


def test_generic_parametrized_field_valid():
    holder = BoxHolder(box=Box(value=7))
    assert holder.box.value == 7


def test_generic_parametrized_field_wrong_inner_type():
    with pytest.raises(TypeError) as error:
        BoxHolder(box=Box(value="x"))
    assert "Wrong type for box:" in error.value.args[0]


def test_generic_parametrized_field_wrong_outer_type():
    with pytest.raises(TypeError) as error:
        BoxHolder(box=123)
    assert "Wrong type for box:" in error.value.args[0]


def test_generic_nested_collection_typevar():
    @dataclass
    class ListBox(Kobject, Generic[_T]):
        items: list[_T]

    @dataclass
    class Holder(Kobject):
        box: ListBox[int]

    assert Holder(box=ListBox(items=[1, 2, 3])).box.items == [1, 2, 3]
    with pytest.raises(TypeError):
        Holder(box=ListBox(items=[1, "x"]))
