from dataclasses import dataclass
from enum import IntEnum
from typing import List, Tuple, Union, Optional, Dict, Coroutine, Callable

import pytest

from kobject import Kobject


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
        class StubDataClass(Kobject):
            a_int: int
            a_bool: bool
            a_str: str
            a_float: float
            a_object: StubInstance

        return StubDataClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_int: int
            a_bool: bool
            a_str: str
            a_float: float
            a_object: StubInstance

            def __init__(
                self,
                a_int: int,
                a_bool: bool,
                a_str: str,
                a_float: float,
                a_object: StubInstance,
            ):
                self.a_int = a_int
                self.a_bool = a_bool
                self.a_str = a_str
                self.a_float = a_float
                self.a_object = a_object
                self.__post_init__()

        return StubClass


def test_simple_attr_error(simple_attr):
    with pytest.raises(TypeError) as error:

        class E:
            pass

        a_int = ""
        a_bool = 2
        a_str = 1.0
        a_float = True
        a_object = E()
        simple_attr(
            a_int=a_int,
            a_bool=a_bool,
            a_str=a_str,
            a_float=a_float,
            a_object=a_object,
        )
    assert error.type == TypeError
    assert error.value.args == (
        "Validation Errors:\n"
        "    'a_int' : Wrong type! Expected <class 'int'> but giving <class 'str'>\n"
        "    'a_bool' : Wrong type! Expected <class 'bool'> but giving <class 'int'>\n"
        "    'a_str' : Wrong type! Expected <class 'str'> but giving <class 'float'>\n"
        "    'a_float' : Wrong type! Expected <class 'float'> but giving <class 'bool'>\n"
        "    'a_object' : Wrong type! Expected <class 'tests.kobject.test_main.StubInstance'> "
        "but giving <class 'tests.kobject.test_main.test_simple_attr_error.<locals>.E'>\n",
    )


def test_simple_attr(simple_attr):
    a_int = 1
    a_bool = True
    a_str = "a"
    a_float = 1.0
    a_object = StubInstance(a_int=1)
    instance = simple_attr(
        a_int=a_int,
        a_bool=a_bool,
        a_str=a_str,
        a_float=a_float,
        a_object=a_object,
    )
    assert instance.a_int == a_int
    assert instance.a_bool == a_bool
    assert instance.a_str == a_str
    assert instance.a_float == a_float
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
        class StubDataClass(Kobject):
            a_list_int: List[int]
            a_tuple_object: Tuple[StubInstance]

        return StubDataClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_list_int: List[int]
            a_tuple_object: Tuple[StubInstance]

            def __init__(
                self, a_list_int: List[int], a_tuple_object: Tuple[StubInstance]
            ):
                self.a_list_int = a_list_int
                self.a_tuple_object = a_tuple_object
                self.__post_init__()

        return StubClass


def test_attr_with_content_error(attr_with_content):
    with pytest.raises(TypeError) as error:

        class E:
            pass

        a_list_int = [1, 2, "", 3, ""]
        a_object = E()
        a_tuple_object = (a_object,)
        attr_with_content(a_list_int=a_list_int, a_tuple_object=a_tuple_object)
    assert error.type == TypeError
    assert error.value.args == (
        "Validation Errors:\n"
        "    'a_list_int' : Wrong type! Expected (<class 'int'>,) but giving <class 'str'> on index 2\n"
        "    'a_list_int' : Wrong type! Expected (<class 'int'>,) but giving <class 'str'> on index 4\n"
        "    'a_tuple_object' : Wrong type! Expected (<class 'tests.kobject.test_main.StubInstance'>,)"
        " but giving <class 'tests.kobject.test_main.test_attr_with_content_error.<locals>.E'> on index 0\n",
    )


def test_attr_with_content(attr_with_content):
    a_list_int = [1, 2, 4, 3, 5]
    a_object = StubInstance(a_int=1)
    a_tuple_object = (a_object,)

    instance = attr_with_content(a_list_int=a_list_int, a_tuple_object=a_tuple_object)
    assert instance.a_list_int == a_list_int
    assert instance.a_tuple_object == a_tuple_object


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def not_real_type_attr(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubDataClass(Kobject):
            a_union_int_bool: Union[int | bool]
            a_optional_str: Optional[str]

        return StubDataClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_union_int_bool: Union[int | bool]
            a_optional_str: Optional[str]

            def __init__(
                self, a_union_int_bool: Union[int | bool], a_optional_str: Optional[str]
            ):
                self.a_union_int_bool = a_union_int_bool
                self.a_optional_str = a_optional_str
                self.__post_init__()

        return StubClass


def test_not_real_type_attr_content_error(not_real_type_attr):
    with pytest.raises(TypeError) as error:
        a_union_int_bool = "a_str"
        a_optional_str = 1
        not_real_type_attr(
            a_union_int_bool=a_union_int_bool, a_optional_str=a_optional_str
        )
    assert error.type == TypeError
    assert error.value.args == (
        "Validation Errors:\n"
        "    'a_union_int_bool' : Wrong type! Expected (<class 'int'>, <class 'bool'>) but giving <class 'str'>\n"
        "    'a_optional_str' : Wrong type! Expected (<class 'str'>, <class 'NoneType'>) but giving <class 'int'>\n",
    )


def test_not_real_type_attr_content_set_1(not_real_type_attr):
    a_union_int_bool = 2
    a_optional_str = None
    instance = not_real_type_attr(
        a_union_int_bool=a_union_int_bool, a_optional_str=a_optional_str
    )
    assert instance.a_union_int_bool == a_union_int_bool
    assert instance.a_optional_str == a_optional_str


def test_not_real_type_attr_content_set_2(not_real_type_attr):
    a_union_int_bool = True
    a_optional_str = "a_str"
    instance = not_real_type_attr(
        a_union_int_bool=a_union_int_bool, a_optional_str=a_optional_str
    )
    assert instance.a_union_int_bool == a_union_int_bool
    assert instance.a_optional_str == a_optional_str


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def invalid_type_attr(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubDataClass(Kobject):
            a_dict: Union[int | dict]
            b_dict: Optional[dict]
            c_dict: dict
            d_dict: Union[int | Dict]
            e_dict: Optional[Dict]
            f_dict: Dict

        return StubDataClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_dict: Union[int | dict]
            b_dict: Optional[dict]
            c_dict: dict
            d_dict: Union[int | Dict]
            e_dict: Optional[Dict]
            f_dict: Dict

            def __init__(
                self,
                a_dict: Union[int | dict],
                b_dict: Optional[dict],
                c_dict: dict,
                d_dict: Union[int | Dict],
                e_dict: Optional[Dict],
                f_dict: Dict,
            ):
                self.a_dict = a_dict
                self.b_dict = b_dict
                self.c_dict = c_dict
                self.d_dict = d_dict
                self.e_dict = e_dict
                self.f_dict = f_dict
                self.__post_init__()

        return StubClass


def test_invalid_type_attr_content_error(invalid_type_attr):
    with pytest.raises(TypeError) as error:
        a_dict = ""
        b_dict = ""
        c_dict = ""
        d_dict = ""
        e_dict = ""
        f_dict = ""
        invalid_type_attr(
            a_dict=a_dict,
            b_dict=b_dict,
            c_dict=c_dict,
            d_dict=d_dict,
            e_dict=e_dict,
            f_dict=f_dict,
        )
    assert error.type == TypeError
    assert error.value.args == (
        "Validation Errors:\n"
        "    'a_dict' : Invalid type! The attribute 'a_dict' is a <class 'dict'>\n"
        "    'b_dict' : Invalid type! The attribute 'b_dict' is a <class 'dict'>\n"
        "    'c_dict' : Invalid type! The attribute 'c_dict' is a <class 'dict'>\n "
        "   'd_dict' : Invalid type! The attribute 'd_dict' is a <class 'dict'>\n"
        "    'e_dict' : Invalid type! The attribute 'e_dict' is a <class 'dict'>\n"
        "    'f_dict' : Invalid type! The attribute 'f_dict' is a <class 'dict'>\n",
    )


def test_invalid_type_attr_content(invalid_type_attr):
    with pytest.raises(TypeError) as error:
        a_dict = {}
        b_dict = {}
        c_dict = {}
        d_dict = {}
        e_dict = {}
        f_dict = {}
        invalid_type_attr(
            a_dict=a_dict,
            b_dict=b_dict,
            c_dict=c_dict,
            d_dict=d_dict,
            e_dict=e_dict,
            f_dict=f_dict,
        )
    assert error.type == TypeError
    assert error.value.args == (
        "Validation Errors:\n"
        "    'a_dict' : Invalid type! The attribute 'a_dict' is a <class 'dict'>\n"
        "    'b_dict' : Invalid type! The attribute 'b_dict' is a <class 'dict'>\n"
        "    'c_dict' : Invalid type! The attribute 'c_dict' is a <class 'dict'>\n "
        "   'd_dict' : Invalid type! The attribute 'd_dict' is a <class 'dict'>\n"
        "    'e_dict' : Invalid type! The attribute 'e_dict' is a <class 'dict'>\n"
        "    'f_dict' : Invalid type! The attribute 'f_dict' is a <class 'dict'>\n",
    )


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def callables_attr(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubDataClass(Kobject):
            a_coroutine: Coroutine
            a_callable: Callable
            b_callable: Callable

        return StubDataClass
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
    assert error.type == TypeError
    assert error.value.args == (
        "Validation Errors:\n"
        "    'a_coroutine' : Wrong type! Expected <class 'collections.abc.Coroutine'> but giving <class 'int'>\n"
        "    'a_callable' : Wrong type! Expected <class 'collections.abc.Callable'> but giving <class 'int'>\n"
        "    'b_callable' : Wrong type! Expected <class 'collections.abc.Callable'> but giving <class 'int'>\n",
    )


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
        class StubDataClass(Kobject):
            a_list_union_bool_str: List[Union[bool, str]]
            a_list_optional_int: List[Optional[int]]

        return StubDataClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_list_union_bool_str: List[Union[bool, str]]
            a_list_optional_int: List[Optional[int]]

            def __init__(
                self,
                a_list_union_bool_str: List[Union[bool, str]],
                a_list_optional_int: List[Optional[int]],
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
        class StubDataClass(Kobject):
            a_bool: bool = 2

        return StubDataClass
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
    assert error.type == TypeError
    assert error.value.args == (
        "Validation Errors:\n    'a_bool' : Wrong type! Expected <class 'bool'> but giving <class 'str'>\n",
    )


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
    Kobject.set_custom_exception(None)
    if request.param == ClassType.DATACLASS:

        @dataclass
        class StubDataClass(Kobject):
            a_bool: bool

        return StubDataClass
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
    Kobject.set_custom_exception(CustomException)
    with pytest.raises(CustomException) as c_error:
        custom_exception(a_bool="")
    error_message = "Validation Errors:\n    'a_bool' : Wrong type! Expected <class 'bool'> but giving <class 'str'>\n"
    assert t_error.value.args[0] == error_message
    assert c_error.value.args[0] == error_message
