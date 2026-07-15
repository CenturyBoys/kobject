"""Tests for the pluggable JSON backend (orjson when available, else stdlib)."""

from dataclasses import dataclass

import pytest

from kobject import Kobject, _json


@dataclass
class Simple(Kobject):
    a_int: int
    a_list: list[int]
    a_dict: dict[str, int]


def test_dumps_loads_round_trip_active_backend():
    payload = _json.dumps({"a": 1, "b": [1, 2]}, default=str)
    assert isinstance(payload, bytes)
    assert _json.loads(payload) == {"a": 1, "b": [1, 2]}


def test_to_json_compact_output_matches_across_backends():
    instance = Simple(a_int=1, a_list=[1, 2], a_dict={"a": 1})
    assert instance.to_json() == b'{"a_int":1,"a_list":[1,2],"a_dict":{"a":1}}'


def test_stdlib_backend_forced(monkeypatch):
    # Force the stdlib branch regardless of whether orjson is installed.
    monkeypatch.setattr(_json, "_HAS_ORJSON", False)
    payload = _json.dumps({"n": "café"}, default=str)
    # stdlib escapes non-ASCII with \uXXXX.
    assert payload == b'{"n":"caf\\u00e9"}'
    assert _json.loads(payload) == {"n": "café"}


def test_orjson_backend_when_available(monkeypatch):
    orjson = pytest.importorskip("orjson")
    monkeypatch.setattr(_json, "_HAS_ORJSON", True)
    monkeypatch.setattr(_json, "orjson", orjson, raising=False)
    payload = _json.dumps({"n": "café"}, default=str)
    # orjson emits raw UTF-8 for non-ASCII strings.
    assert payload == b'{"n":"caf\xc3\xa9"}'
    assert _json.loads(payload) == {"n": "café"}
