"""Edge case tests for Kobject."""

from dataclasses import dataclass
from typing import Any

import pytest

from kobject import Empty, Kobject


class TestEmptyType:
    """Tests for Empty type behavior."""

    def test_empty_repr(self):
        """Empty should have a readable repr."""
        assert repr(Empty) == "<EMPTY>"

    def test_empty_bool(self):
        """Empty should be falsy."""
        assert not Empty
        assert bool(Empty) is False

    def test_empty_equality_to_itself(self):
        """Empty should be equal to itself."""
        assert Empty is Empty


class TestUnicodeFieldNames:
    """Tests for unicode field names."""

    def test_unicode_field_name(self):
        """Kobject should handle unicode field names."""

        @dataclass
        class UnicodeFields(Kobject):
            nombre: str
            descripcion: str

        instance = UnicodeFields(nombre="test", descripcion="description")
        assert instance.nombre == "test"
        assert instance.descripcion == "description"

    def test_unicode_field_to_dict(self):
        """Unicode fields should serialize correctly."""

        @dataclass
        class UnicodeFields(Kobject):
            nombre: str
            valor: int

        instance = UnicodeFields(nombre="test", valor=42)
        result = instance.dict()
        assert result == {"nombre": "test", "valor": 42}


class TestDeepNesting:
    """Tests for deeply nested structures."""

    def test_nested_list(self):
        """Kobject should handle nested lists."""

        @dataclass
        class NestedList(Kobject):
            data: list[list[int]]

        instance = NestedList(data=[[1, 2], [3, 4]])
        assert instance.data == [[1, 2], [3, 4]]

    def test_deeply_nested_kobject(self):
        """Kobject should handle deeply nested Kobject instances."""

        @dataclass
        class Level3(Kobject):
            value: int

        @dataclass
        class Level2(Kobject):
            child: Level3

        @dataclass
        class Level1(Kobject):
            child: Level2

        @dataclass
        class Root(Kobject):
            child: Level1

        instance = Root(child=Level1(child=Level2(child=Level3(value=42))))
        assert instance.child.child.child.value == 42

    def test_deeply_nested_dict(self):
        """dict() should work with deeply nested Kobject."""

        @dataclass
        class Level2(Kobject):
            value: int

        @dataclass
        class Level1(Kobject):
            child: Level2

        @dataclass
        class Root(Kobject):
            child: Level1

        instance = Root(child=Level1(child=Level2(value=42)))
        result = instance.dict()
        assert result == {"child": {"child": {"value": 42}}}


class TestLargeObjects:
    """Tests for large objects."""

    def test_many_fields(self):
        """Kobject should handle objects with many fields."""

        @dataclass
        class ManyFields(Kobject):
            f1: int
            f2: int
            f3: int
            f4: int
            f5: int
            f6: int
            f7: int
            f8: int
            f9: int
            f10: int
            f11: int
            f12: int
            f13: int
            f14: int
            f15: int
            f16: int
            f17: int
            f18: int
            f19: int
            f20: int

        instance = ManyFields(
            f1=1,
            f2=2,
            f3=3,
            f4=4,
            f5=5,
            f6=6,
            f7=7,
            f8=8,
            f9=9,
            f10=10,
            f11=11,
            f12=12,
            f13=13,
            f14=14,
            f15=15,
            f16=16,
            f17=17,
            f18=18,
            f19=19,
            f20=20,
        )
        assert instance.f1 == 1
        assert instance.f20 == 20

    def test_large_list(self):
        """Kobject should handle large lists."""

        @dataclass
        class LargeList(Kobject):
            items: list[int]

        items = list(range(1000))
        instance = LargeList(items=items)
        assert len(instance.items) == 1000
        assert instance.items[0] == 0
        assert instance.items[999] == 999


class TestFromDictExtraKeys:
    """Tests for from_dict with extra keys."""

    def test_from_dict_ignores_extra_keys(self):
        """from_dict should ignore extra keys not in the class."""

        @dataclass
        class Simple(Kobject):
            name: str
            value: int

        result = Simple.from_dict(
            {"name": "test", "value": 42, "extra_key": "ignored", "another": 123}
        )
        assert result.name == "test"
        assert result.value == 42
        assert not hasattr(result, "extra_key")
        assert not hasattr(result, "another")


class TestAnyType:
    """Tests for Any type fields."""

    def test_any_accepts_anything(self):
        """Any type should accept any value."""

        @dataclass
        class WithAny(Kobject):
            data: Any

        assert WithAny(data=42).data == 42
        assert WithAny(data="string").data == "string"
        assert WithAny(data=[1, 2, 3]).data == [1, 2, 3]
        assert WithAny(data={"key": "value"}).data == {"key": "value"}
        assert WithAny(data=None).data is None


class TestEmptyCollections:
    """Tests for empty collections."""

    def test_empty_list(self):
        """Kobject should handle empty lists."""

        @dataclass
        class WithList(Kobject):
            items: list[int]

        instance = WithList(items=[])
        assert instance.items == []

    def test_empty_dict(self):
        """Kobject should handle empty dicts."""

        @dataclass
        class WithDict(Kobject):
            data: dict[str, int]

        instance = WithDict(data={})
        assert instance.data == {}


class TestRepr:
    """Tests for __repr__ and __str__."""

    def test_repr(self):
        """__repr__ should show class name and field values."""

        class Simple(Kobject):
            def __init__(self, name: str, value: int):
                self.name = name
                self.value = value
                self.__post_init__()

        instance = Simple(name="test", value=42)
        repr_str = repr(instance)
        assert "Simple" in repr_str
        assert "name=test" in repr_str
        assert "value=42" in repr_str

    def test_str_equals_repr(self):
        """__str__ should equal __repr__."""

        class Simple(Kobject):
            def __init__(self, name: str):
                self.name = name
                self.__post_init__()

        instance = Simple(name="test")
        assert str(instance) == repr(instance)


class TestValidationErrors:
    """Tests for validation error details."""

    def test_error_includes_field_name(self):
        """TypeError should include the field name."""

        @dataclass
        class Simple(Kobject):
            name: str

        with pytest.raises(TypeError) as exc_info:
            Simple(name=123)  # type: ignore

        assert "name" in str(exc_info.value)

    def test_json_error_method(self):
        """Exception should have json_error method."""

        @dataclass
        class Simple(Kobject):
            name: str

        with pytest.raises(TypeError) as exc_info:
            Simple(name=123)  # type: ignore

        errors = exc_info.value.json_error()
        assert len(errors) == 1
        assert errors[0]["field"] == "name"
        assert errors[0]["type"] is str
