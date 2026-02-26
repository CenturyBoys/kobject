"""Additional tests for validation.py coverage."""

from dataclasses import dataclass

import pytest

from kobject import Kobject


@dataclass
class Item(Kobject):
    """Test item."""

    value: int


class TestUnionValidationInCollections:
    """Tests for Union type validation failures in collections."""

    def test_list_union_wrong_type(self):
        """Test list[int | str] with wrong type (float)."""

        @dataclass
        class Container(Kobject):
            items: list[int | str]

        with pytest.raises(TypeError) as exc:
            Container(items=[1.5])  # float is neither int nor str

        assert "items" in str(exc.value)

    def test_dict_value_union_wrong_type(self):
        """Test dict[str, int | None] with wrong value type."""

        @dataclass
        class Container(Kobject):
            data: dict[str, int | None]

        with pytest.raises(TypeError) as exc:
            Container(data={"key": "value"})  # str is neither int nor None

        assert "data" in str(exc.value)

    def test_tuple_union_wrong_type(self):
        """Test tuple[int | str, bool] with wrong type in first position."""

        @dataclass
        class Container(Kobject):
            pair: tuple[int | str, bool]

        with pytest.raises(TypeError) as exc:
            Container(pair=(1.5, True))  # float is neither int nor str

        assert "pair" in str(exc.value)

    def test_nested_union_all_options_fail(self):
        """Test Union where all options fail validation."""

        @dataclass
        class Container(Kobject):
            value: int | str | bool

        with pytest.raises(TypeError) as exc:
            Container(value=[])  # list is not int, str, or bool

        assert "value" in str(exc.value)


class TestSpecialFormValidation:
    """Tests for special form (Union/Optional) validation."""

    def test_union_first_option_matches(self):
        """Test Union where first option matches."""

        @dataclass
        class Container(Kobject):
            value: int | str | bool

        obj = Container(value=42)
        assert obj.value == 42

    def test_union_second_option_matches(self):
        """Test Union where second option matches."""

        @dataclass
        class Container(Kobject):
            value: int | str | bool

        obj = Container(value="hello")
        assert obj.value == "hello"

    def test_union_last_option_matches(self):
        """Test Union where last option matches."""

        @dataclass
        class Container(Kobject):
            value: int | str | bool

        obj = Container(value=True)
        assert obj.value is True

    def test_optional_with_none(self):
        """Test Optional[T] with None value."""

        @dataclass
        class Container(Kobject):
            value: str | None

        obj = Container(value=None)
        assert obj.value is None

    def test_optional_with_value(self):
        """Test Optional[T] with actual value."""

        @dataclass
        class Container(Kobject):
            value: str | None

        obj = Container(value="hello")
        assert obj.value == "hello"


class TestGenericTypes:
    """Tests for generic type validation coverage."""

    def test_set_type_valid(self):
        """Test set type validation."""

        @dataclass
        class Container(Kobject):
            items: set[int]

        obj = Container(items={1, 2, 3})
        assert obj.items == {1, 2, 3}

    def test_set_type_invalid(self):
        """Test set type validation with wrong type."""

        @dataclass
        class Container(Kobject):
            items: set[int]

        with pytest.raises(TypeError) as exc:
            Container(items="not a set")

        assert "items" in str(exc.value)


class TestEdgeCases:
    """Edge case tests for validation."""

    def test_deeply_nested_union(self):
        """Test deeply nested Union types."""

        @dataclass
        class Container(Kobject):
            items: list[dict[str, int | str | None]]

        obj = Container(items=[{"a": 1}, {"b": "hello"}, {"c": None}])
        assert len(obj.items) == 3

    def test_empty_collections(self):
        """Test empty collections pass validation."""

        @dataclass
        class Container(Kobject):
            items: list[int]
            data: dict[str, int]
            pair: tuple[()]

        obj = Container(items=[], data={}, pair=())
        assert obj.items == []
        assert obj.data == {}
