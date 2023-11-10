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
        class StubClass(Kobject):
            a_int: int
            a_bool: bool
            a_str: str
            a_float: float
            a_object: StubInstance

        return StubClass
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
        "Class 'StubClass' type error:\n"
        " Wrong type for a_int: <class 'int'> != '<class 'str'>'\n"
        " Wrong type for a_bool: <class 'bool'> != '<class 'int'>'\n"
        " Wrong type for a_str: <class 'str'> != '<class 'float'>'\n"
        " Wrong type for a_float: <class 'float'> != '<class 'bool'>'\n"
        " Wrong type for a_object: <class 'tests.kobject.validator.test_main.StubInstance'> != "
        "'<class 'tests.kobject.validator.test_main.test_simple_attr_error.<locals>.E'>'",
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
        class StubClass(Kobject):
            a_list_int: List[int]
            a_tuple_object: Tuple[StubInstance]
            a_dict_str_optional_int: Dict[str, None | int]

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_list_int: List[int]
            a_tuple_object: Tuple[StubInstance]
            a_dict_str_optional_int: Dict[str, None | int]

            def __init__(
                self,
                a_list_int: List[int],
                a_tuple_object: Tuple[StubInstance],
                a_dict_str_optional_int: Dict[str, None | int],
            ):
                self.a_list_int = a_list_int
                self.a_tuple_object = a_tuple_object
                self.a_dict_str_optional_int = a_dict_str_optional_int
                self.__post_init__()

        return StubClass


def test_attr_with_content_error(attr_with_content):
    with pytest.raises(TypeError) as error:

        class E:
            pass

        a_list_int = [1, 2, "", 3, ""]
        a_object = E()
        a_tuple_object = (a_object,)
        a_dict_str_optional_int = {"str": True, 1: "str", 2: True}
        attr_with_content(
            a_list_int=a_list_int,
            a_tuple_object=a_tuple_object,
            a_dict_str_optional_int=a_dict_str_optional_int,
        )
    assert error.type == TypeError
    assert error.value.args == (
        "Class 'StubClass' type error:\n"
        " Wrong type for a_list_int: typing.List[int] != '<class 'list'>'\n"
        " Wrong type for a_tuple_object: typing.Tuple[tests.kobject.validator.test_main.StubInstan"
        "ce] != '<class 'tuple'>'\n"
        " Wrong type for a_dict_str_optional_int: typing.Dict[str, None | int] != '<class 'dict'>'",
    )


def test_attr_with_content(attr_with_content):
    a_list_int = [1, 2, 4, 3, 5]
    a_object = StubInstance(a_int=1)
    a_tuple_object = (a_object,)
    a_dict_str_optional_int = {"str": 2}

    instance = attr_with_content(
        a_list_int=a_list_int,
        a_tuple_object=a_tuple_object,
        a_dict_str_optional_int=a_dict_str_optional_int,
    )
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
        class StubClass(Kobject):
            a_union_int_bool: Union[int | bool]
            a_optional_str: Optional[str]
            a_optional_int: int | None

        return StubClass
    elif request.param == ClassType.DEFAULT:

        class StubClass(Kobject):
            a_union_int_bool: Union[int | bool]
            a_optional_str: Optional[str]
            a_optional_int: int | None

            def __init__(
                self,
                a_union_int_bool: Union[int | bool],
                a_optional_str: Optional[str],
                a_optional_int: int | None,
            ):
                self.a_union_int_bool = a_union_int_bool
                self.a_optional_str = a_optional_str
                self.a_optional_int = a_optional_int
                self.__post_init__()

        return StubClass


def test_not_real_type_attr_content_error(not_real_type_attr):
    with pytest.raises(TypeError) as error:
        a_union_int_bool = "a_str"
        a_optional_str = 1
        a_optional_int = "lala"
        not_real_type_attr(
            a_union_int_bool=a_union_int_bool,
            a_optional_str=a_optional_str,
            a_optional_int=a_optional_int,
        )
    assert error.type == TypeError
    assert error.value.args == (
        "Class 'StubClass' type error:\n"
        " Wrong type for a_union_int_bool: typing.Union[int, bool] != '<class 'str'>'\n"
        " Wrong type for a_optional_str: typing.Optional[str] != '<class 'int'>'\n"
        " Wrong type for a_optional_int: int | None != '<class 'str'>'",
    )


def test_not_real_type_attr_content_set_1(not_real_type_attr):
    a_union_int_bool = 2
    a_optional_str = None
    a_optional_int = None
    instance = not_real_type_attr(
        a_union_int_bool=a_union_int_bool,
        a_optional_str=a_optional_str,
        a_optional_int=a_optional_int,
    )
    assert instance.a_union_int_bool == a_union_int_bool
    assert instance.a_optional_str == a_optional_str


def test_not_real_type_attr_content_set_2(not_real_type_attr):
    a_union_int_bool = True
    a_optional_str = "a_str"
    a_optional_int = 1
    instance = not_real_type_attr(
        a_union_int_bool=a_union_int_bool,
        a_optional_str=a_optional_str,
        a_optional_int=a_optional_int,
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
    assert error.type == TypeError
    assert error.value.args == (
        "Class 'StubClass' type error:\n"
        " Wrong type for a_coroutine: typing.Coroutine != '<class 'int'>'\n"
        " Wrong type for a_callable: typing.Callable != '<class 'int'>'\n"
        " Wrong type for b_callable: typing.Callable != '<class 'int'>'",
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
        class StubClass(Kobject):
            a_list_union_bool_str: List[Union[bool, str]]
            a_list_optional_int: List[Optional[int]]

        return StubClass
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
    assert error.type == TypeError
    assert error.value.args == (
        "Class 'StubClass' type error:\n"
        " Wrong type for a_bool: <class 'bool'> != '<class 'str'>'",
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
        "Class 'StubClass' type error:\n"
        " Wrong type for a_bool: <class 'bool'> != '<class 'str'>'",
    )
    assert c_error.value.args == (
        "Class 'StubClass' type error:\n"
        " Wrong type for a_bool: <class 'bool'> != '<class 'str'>'",
    )


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
        "Class 'StubClass' type error:\n"
        " Wrong type for a_bool: <class 'bool'> != '<class 'str'>'",
    )


def test_lazy_validator_off(lazy_validator):
    Kobject.set_lazy_type_check(False)
    with pytest.raises(TypeError) as t_error:
        lazy_validator(a_bool="", b_bool="")
    assert t_error.value.args == (
        "Class 'StubClass' type error:\n"
        " Wrong type for a_bool: <class 'bool'> != '<class 'str'>'\n"
        " Wrong type for b_bool: <class 'bool'> != '<class 'str'>'",
    )
