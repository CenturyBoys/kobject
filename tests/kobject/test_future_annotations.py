"""Tests for classes using from __future__ import annotations."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from kobject import Kobject


@dataclass
class DataclassModel(Kobject):
    name: str
    age: int
    score: float | None = None


class RegularModel(Kobject):
    def __init__(self, name: str, age: int, score: float | None = None):
        self.name = name
        self.age = age
        self.score = score
        self.__post_init__()


def test_dataclass_with_future_annotations():
    obj = DataclassModel(name="Alice", age=30)
    assert obj.name == "Alice"
    assert obj.age == 30


def test_dataclass_with_future_annotations_error():
    with pytest.raises(TypeError):
        DataclassModel(name="Alice", age="not_an_int")


def test_regular_class_with_future_annotations():
    obj = RegularModel(name="Bob", age=25, score=9.5)
    assert obj.name == "Bob"
    assert obj.age == 25


def test_regular_class_with_future_annotations_error():
    with pytest.raises(TypeError):
        RegularModel(name="Bob", age="not_an_int")


def test_optional_field_with_future_annotations():
    obj = DataclassModel(name="Carol", age=20, score=None)
    assert obj.score is None


def test_from_dict_with_future_annotations():
    obj = DataclassModel.from_dict({"name": "Dave", "age": 40})
    assert obj.name == "Dave"


def test_to_json_with_future_annotations():
    obj = DataclassModel(name="Eve", age=35)
    json_bytes = obj.to_json()
    assert b'"name":"Eve"' in json_bytes
