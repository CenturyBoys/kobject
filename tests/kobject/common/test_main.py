from dataclasses import dataclass, FrozenInstanceError
from inspect import _empty
from typing import List

import pytest

from kobject.common import FieldMeta, InheritanceFieldMeta


def test_slots_frozen():
    filed_meta = FieldMeta.new_one("a", bool, _empty)
    assert filed_meta.__slots__ == (
        "name",
        "annotation",
        "required",
        "have_default_value",
        "default",
    )
    with pytest.raises(FrozenInstanceError):
        filed_meta.name = ""


def test_field_metadata_new_one():
    a = List[dict[str, int]]
    filed_meta = FieldMeta.new_one("a", a, _empty)
    assert filed_meta.name == "a"
    assert filed_meta.annotation == a
    assert filed_meta.required is True
    assert filed_meta.default == _empty
    assert filed_meta.have_default_value is False


def test_get_generic_field_meta():
    a = List[dict[str, int]]
    filed_meta = FieldMeta.get_generic_field_meta(a)
    assert id(filed_meta) == id(FieldMeta.get_generic_field_meta(a))
    assert filed_meta.name == ""
    assert filed_meta.annotation == a
    assert filed_meta.required is True
    assert filed_meta.default == _empty
    assert filed_meta.have_default_value is False


def test__with_field_map():
    @dataclass
    class A(InheritanceFieldMeta):
        a_int: int

    obj = A(10)
    fields1 = obj._with_field_map()
    fields2 = obj._with_field_map()
    for i in zip(fields1, fields2):
        assert id(i[0]) == id(i[1])
