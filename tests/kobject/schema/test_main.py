"""Tests for JSON Schema generation."""

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Any
from uuid import UUID

import pytest

from kobject import Kobject
from kobject.schema import DocstringMeta, JSONSchemaGenerator, parse_docstring


class ClassType(IntEnum):
    DATACLASS = 0
    DEFAULT = 1


# =============================================================================
# Docstring Parsing Tests
# =============================================================================


def test_parse_docstring_empty():
    result = parse_docstring(None)
    assert result == DocstringMeta()

    result = parse_docstring("")
    assert result == DocstringMeta()


def test_parse_docstring_title_only():
    docstring = "This is the title."
    result = parse_docstring(docstring)
    assert result.title == "This is the title."
    assert result.description is None
    assert result.field_descriptions == {}
    assert result.examples == []


def test_parse_docstring_title_and_description():
    docstring = """
    Short title.

    This is a longer description that
    spans multiple lines.
    """
    result = parse_docstring(docstring)
    assert result.title == "Short title."
    assert (
        result.description == "This is a longer description that spans multiple lines."
    )


def test_parse_docstring_with_params():
    docstring = """
    User model.

    :param name: The user's full name.
    :param age: The user's age in years.
    """
    result = parse_docstring(docstring)
    assert result.title == "User model."
    assert result.field_descriptions == {
        "name": "The user's full name.",
        "age": "The user's age in years.",
    }


def test_parse_docstring_with_multiline_param():
    docstring = """
    Model.

    :param field: This is a long description
        that continues on the next line.
    """
    result = parse_docstring(docstring)
    assert result.field_descriptions["field"] == (
        "This is a long description that continues on the next line."
    )


def test_parse_docstring_with_example():
    docstring = """
    Order model.

    :param user_id: ID of the user.
    :example: {"user_id": 123}
    """
    result = parse_docstring(docstring)
    assert result.title == "Order model."
    assert result.field_descriptions == {"user_id": "ID of the user."}
    assert result.examples == [{"user_id": 123}]


def test_parse_docstring_with_multiple_examples():
    docstring = """
    Model.

    :example: {"a": 1}
    :example: {"a": 2, "b": 3}
    """
    result = parse_docstring(docstring)
    assert result.examples == [{"a": 1}, {"a": 2, "b": 3}]


def test_parse_docstring_invalid_example_json():
    docstring = """
    Model.

    :example: {invalid json}
    """
    result = parse_docstring(docstring)
    assert result.examples == []


# =============================================================================
# Basic Type Schema Tests
# =============================================================================


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def basic_types_class(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class BasicTypes(Kobject):
            a_str: str
            a_int: int
            a_float: float
            a_bool: bool

        return BasicTypes
    elif request.param == ClassType.DEFAULT:

        class BasicTypes(Kobject):
            def __init__(self, a_str: str, a_int: int, a_float: float, a_bool: bool):
                self.a_str = a_str
                self.a_int = a_int
                self.a_float = a_float
                self.a_bool = a_bool
                self.__post_init__()

        return BasicTypes


def test_basic_types_schema(basic_types_class):
    schema = basic_types_class.json_schema()

    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"a_str", "a_int", "a_float", "a_bool"}

    props = schema["properties"]
    assert props["a_str"] == {"type": "string"}
    assert props["a_int"] == {"type": "integer"}
    assert props["a_float"] == {"type": "number"}
    assert props["a_bool"] == {"type": "boolean"}


# =============================================================================
# Optional and Default Value Tests
# =============================================================================


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def optional_and_defaults_class(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class OptionalDefaults(Kobject):
            required_field: str
            optional_field: str | None
            default_str: str = "default"
            default_int: int = 42
            default_none: str | None = None

        return OptionalDefaults
    elif request.param == ClassType.DEFAULT:

        class OptionalDefaults(Kobject):
            def __init__(
                self,
                required_field: str,
                optional_field: str | None,
                default_str: str = "default",
                default_int: int = 42,
                default_none: str | None = None,
            ):
                self.required_field = required_field
                self.optional_field = optional_field
                self.default_str = default_str
                self.default_int = default_int
                self.default_none = default_none
                self.__post_init__()

        return OptionalDefaults


def test_optional_and_defaults_schema(optional_and_defaults_class):
    schema = optional_and_defaults_class.json_schema()

    props = schema["properties"]
    required = schema["required"]

    # Required field
    assert "required_field" in required
    assert props["required_field"] == {"type": "string"}

    # Optional field (T | None)
    assert "optional_field" in required
    assert props["optional_field"] == {"anyOf": [{"type": "string"}, {"type": "null"}]}

    # Fields with defaults should NOT be in required
    assert "default_str" not in required
    assert "default_int" not in required
    assert "default_none" not in required

    # Default values should be in schema
    assert props["default_str"]["default"] == "default"
    assert props["default_int"]["default"] == 42
    assert props["default_none"]["default"] is None


# =============================================================================
# Collection Type Tests
# =============================================================================


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def collection_types_class(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class Collections(Kobject):
            a_list: list[int]
            a_dict: dict[str, int]
            a_tuple_fixed: tuple[str, int, bool]
            a_set: set[str]

        return Collections
    elif request.param == ClassType.DEFAULT:

        class Collections(Kobject):
            def __init__(
                self,
                a_list: list[int],
                a_dict: dict[str, int],
                a_tuple_fixed: tuple[str, int, bool],
                a_set: set[str],
            ):
                self.a_list = a_list
                self.a_dict = a_dict
                self.a_tuple_fixed = a_tuple_fixed
                self.a_set = a_set
                self.__post_init__()

        return Collections


def test_collection_types_schema(collection_types_class):
    schema = collection_types_class.json_schema()
    props = schema["properties"]

    # list[int]
    assert props["a_list"] == {"type": "array", "items": {"type": "integer"}}

    # dict[str, int]
    assert props["a_dict"] == {
        "type": "object",
        "additionalProperties": {"type": "integer"},
    }

    # tuple[str, int, bool]
    assert props["a_tuple_fixed"] == {
        "type": "array",
        "prefixItems": [
            {"type": "string"},
            {"type": "integer"},
            {"type": "boolean"},
        ],
        "minItems": 3,
        "maxItems": 3,
    }

    # set[str]
    assert props["a_set"] == {
        "type": "array",
        "items": {"type": "string"},
        "uniqueItems": True,
    }


# =============================================================================
# Enum Tests
# =============================================================================


class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PriorityEnum(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@pytest.fixture(
    params=[
        ClassType.DATACLASS,
        ClassType.DEFAULT,
    ]
)
def enum_class(request):
    if request.param == ClassType.DATACLASS:

        @dataclass
        class WithEnums(Kobject):
            status: StatusEnum
            priority: PriorityEnum

        return WithEnums
    elif request.param == ClassType.DEFAULT:

        class WithEnums(Kobject):
            def __init__(self, status: StatusEnum, priority: PriorityEnum):
                self.status = status
                self.priority = priority
                self.__post_init__()

        return WithEnums


def test_enum_schema(enum_class):
    schema = enum_class.json_schema()
    props = schema["properties"]

    # String enum
    assert props["status"] == {
        "type": "string",
        "enum": ["active", "inactive"],
    }

    # Int enum
    assert props["priority"] == {
        "type": "integer",
        "enum": [1, 2, 3],
    }


# =============================================================================
# Nested Kobject Tests
# =============================================================================


@dataclass
class Address(Kobject):
    """
    Address information.

    :param street: Street name and number.
    :param city: City name.
    """

    street: str
    city: str


@dataclass
class Person(Kobject):
    """
    A person with an address.

    :param name: Person's name.
    :param address: Person's address.
    """

    name: str
    address: Address


def test_nested_kobject_schema():
    schema = Person.json_schema()

    # Check main schema
    assert schema["title"] == "A person with an address."
    assert schema["properties"]["name"] == {
        "type": "string",
        "description": "Person's name.",
    }
    # $ref with description from docstring
    assert schema["properties"]["address"] == {
        "$ref": "#/$defs/Address",
        "description": "Person's address.",
    }

    # Check $defs
    assert "$defs" in schema
    assert "Address" in schema["$defs"]

    address_schema = schema["$defs"]["Address"]
    assert address_schema["type"] == "object"
    assert address_schema["properties"]["street"] == {
        "type": "string",
        "description": "Street name and number.",
    }
    assert address_schema["properties"]["city"] == {
        "type": "string",
        "description": "City name.",
    }


def test_nested_kobject_in_list():
    @dataclass
    class Team(Kobject):
        members: list[Person]

    schema = Team.json_schema()

    assert schema["properties"]["members"] == {
        "type": "array",
        "items": {"$ref": "#/$defs/Person"},
    }
    assert "Person" in schema["$defs"]
    assert "Address" in schema["$defs"]


def test_nested_kobject_optional():
    @dataclass
    class Company(Kobject):
        name: str
        headquarters: Address | None

    schema = Company.json_schema()

    assert schema["properties"]["headquarters"] == {
        "anyOf": [{"$ref": "#/$defs/Address"}, {"type": "null"}]
    }
    assert "Address" in schema["$defs"]


# =============================================================================
# Custom Resolver Tests
# =============================================================================


def test_datetime_resolver():
    @dataclass
    class Event(Kobject):
        created_at: datetime
        event_date: date
        start_time: time

    schema = Event.json_schema()
    props = schema["properties"]

    assert props["created_at"] == {"type": "string", "format": "date-time"}
    assert props["event_date"] == {"type": "string", "format": "date"}
    assert props["start_time"] == {"type": "string", "format": "time"}


def test_uuid_resolver():
    @dataclass
    class Entity(Kobject):
        id: UUID

    schema = Entity.json_schema()
    assert schema["properties"]["id"] == {"type": "string", "format": "uuid"}


def test_decimal_resolver():
    @dataclass
    class Price(Kobject):
        amount: Decimal

    schema = Price.json_schema()
    assert schema["properties"]["amount"] == {
        "type": "string",
        "pattern": r"^-?\d+(\.\d+)?$",
    }


def test_custom_type_resolver():
    class CustomType:
        pass

    Kobject.set_schema_resolver(
        CustomType, lambda t: {"type": "string", "format": "custom"}
    )

    @dataclass
    class WithCustom(Kobject):
        custom_field: CustomType

    schema = WithCustom.json_schema()
    assert schema["properties"]["custom_field"] == {
        "type": "string",
        "format": "custom",
    }


# =============================================================================
# Docstring Integration Tests
# =============================================================================


def test_full_docstring_integration():
    @dataclass
    class Order(Kobject):
        """
        Represents an order in the system.

        :param user_id: ID of the user placing the order.
        :param priority: Whether this is a priority order.
        :example: {"user_id": 123, "priority": true}
        """

        user_id: int
        priority: bool = False

    schema = Order.json_schema()

    assert schema["title"] == "Represents an order in the system."
    assert schema["properties"]["user_id"]["description"] == (
        "ID of the user placing the order."
    )
    assert schema["properties"]["priority"]["description"] == (
        "Whether this is a priority order."
    )
    assert schema["properties"]["priority"]["default"] is False
    assert schema["examples"] == [{"user_id": 123, "priority": True}]


# =============================================================================
# Edge Case Tests
# =============================================================================


def test_no_fields():
    @dataclass
    class Empty(Kobject):
        pass

    schema = Empty.json_schema()
    assert schema["type"] == "object"
    assert schema["properties"] == {}
    assert "required" not in schema


def test_no_docstring():
    # Regular class (not dataclass) has no auto-generated docstring
    class NoDoc(Kobject):
        def __init__(self, field: str):
            self.field = field
            self.__post_init__()

    schema = NoDoc.json_schema()
    assert "title" not in schema
    assert "description" not in schema


def test_any_type():
    @dataclass
    class WithAny(Kobject):
        dynamic: Any

    schema = WithAny.json_schema()
    assert schema["properties"]["dynamic"] == {}


def test_union_multiple_types():
    @dataclass
    class MultiUnion(Kobject):
        value: str | int | bool

    schema = MultiUnion.json_schema()
    assert schema["properties"]["value"] == {
        "anyOf": [
            {"type": "string"},
            {"type": "integer"},
            {"type": "boolean"},
        ]
    }


def test_union_with_none():
    @dataclass
    class UnionNone(Kobject):
        value: str | int | None

    schema = UnionNone.json_schema()
    # Complex union with None - should have all types in anyOf
    assert schema["properties"]["value"] == {
        "anyOf": [
            {"type": "string"},
            {"type": "integer"},
            {"type": "null"},
        ]
    }


def test_non_kobject_raises_error():
    class NotKobject:
        pass

    with pytest.raises(TypeError) as exc:
        JSONSchemaGenerator.generate(NotKobject)

    assert "NotKobject is not a Kobject subclass" in str(exc.value)


def test_list_without_type_arg():
    @dataclass
    class UntypedList(Kobject):
        items: list

    schema = UntypedList.json_schema()
    assert schema["properties"]["items"] == {"type": "array"}


def test_dict_without_type_args():
    @dataclass
    class UntypedDict(Kobject):
        data: dict

    schema = UntypedDict.json_schema()
    assert schema["properties"]["data"] == {"type": "object"}


# =============================================================================
# Thread Safety Test
# =============================================================================


def test_concurrent_schema_generation():
    import threading

    @dataclass
    class ThreadTestClass(Kobject):
        field: str

    results = []
    errors = []

    def generate_schema():
        try:
            schema = ThreadTestClass.json_schema()
            results.append(schema)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=generate_schema) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(results) == 10
    # All schemas should be identical
    for schema in results:
        assert schema["properties"]["field"] == {"type": "string"}


def test_concurrent_resolver_registration():
    import threading

    errors = []
    registered = []

    def register_resolver(i: int):
        try:

            class DynamicType:
                pass

            DynamicType.__name__ = f"DynamicType{i}"
            JSONSchemaGenerator.register_resolver(
                DynamicType, lambda t: {"type": "string", "id": i}
            )
            registered.append(i)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=register_resolver, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(registered) == 10
