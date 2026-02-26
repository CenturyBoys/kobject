# Kobject Architecture

This document describes the internal architecture of Kobject, a Python runtime type validation library.

## Overview

Kobject validates `__init__` parameter types at instantiation time by inspecting the method signature. It supports both dataclasses and regular classes with Python 3.10+.

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Code                                │
│   @dataclass                                                    │
│   class User(Kobject):                                         │
│       name: str                                                 │
│       age: int                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      core.py (Kobject)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ __post_init__│→ │ _with_field  │→ │ __validate_model     │  │
│  │              │  │ _map()       │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                              │                  │
│  ┌──────────────┐  ┌──────────────┐          ▼                  │
│  │ from_json()  │  │ to_json()    │  ┌──────────────────────┐  │
│  │ from_dict()  │  │ dict()       │  │ validation.py        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
kobject/
├── __init__.py       # Entry point, exports, default resolvers
├── _compat.py        # Python version compatibility helpers
├── core.py           # Main Kobject base class
├── fields.py         # FieldMeta dataclass for field metadata
├── schema.py         # JSON Schema Draft 7 generation
├── serialization.py  # JSON encoder/decoder with resolver system
└── validation.py     # Type validation logic
```

## Core Components

### 1. Kobject Base Class (`core.py`)

The main class users inherit from. Key responsibilities:

- **Type Validation**: `__post_init__()` triggers validation via `__validate_model()`
- **Field Caching**: `_with_field_map()` caches field metadata per class
- **Serialization**: `to_json()`, `dict()` for output
- **Deserialization**: `from_json()`, `from_dict()` for input
- **Schema Generation**: `json_schema()` for JSON Schema output
- **Resolver Registration**: `set_decoder_resolver()`, `set_encoder_resolver()`, `set_schema_resolver()`

### 2. Field Metadata (`fields.py`)

`FieldMeta` is a dataclass that holds pre-processed information about each class field:

```python
@dataclass(slots=True)
class FieldMeta:
    name: str                    # Field name
    annotation: type[Any]        # Type annotation
    have_default_value: bool     # Whether a default exists
    default: Any                 # The default value (or EMPTY)
```

### 3. Validation Module (`validation.py`)

Pure functions for type checking:

- `_validate_field_value()`: Entry point for validating a single field
- `_validate_special_form()`: Handles Union/Optional types
- `_validate_dict()`: Validates Dict[K, V] types
- `_validate_tuple()`: Validates Tuple types with fixed length
- `_validate_list()`: Validates List[T] types

### 4. Serialization Module (`serialization.py`)

JSON encoding/decoding with extensibility:

- `JSONEncoder`: Custom encoder with resolver support
- `JSONDecoder`: Type casting for deserialization
- `_resolve_list()`, `_resolve_tuple()`, `_resolve_dict()`: Collection handlers

### 5. Schema Module (`schema.py`)

JSON Schema Draft 7 generation:

- `JSONSchemaGenerator`: Main generator class
- `parse_docstring()`: Extracts metadata from reST-style docstrings
- `DocstringMeta`: Dataclass holding parsed docstring info

## Data Flow

### Validation Flow

```
User creates instance
        │
        ▼
__post_init__() called (by dataclass or manually)
        │
        ▼
__validate_model()
        │
        ├─── _with_field_map() → Returns cached FieldMeta list
        │
        └─── For each field:
                │
                ▼
            _validate_field_value(value, field)
                │
                ├─── value == default? → Valid
                ├─── No annotation? → Valid
                ├─── Not generic? → isinstance() check
                ├─── Union type? → _validate_special_form()
                ├─── Dict type? → _validate_dict()
                ├─── List type? → _validate_list()
                └─── Tuple type? → _validate_tuple()
                        │
                        ▼
                Returns True/False
        │
        ▼
If any invalid → Raise exception with json_error() method
```

### Serialization Flow

```
obj.to_json() / obj.dict()
        │
        ▼
obj._dict(resolver)
        │
        ├─── For each field:
        │       │
        │       ▼
        │   resolve(attr_value)
        │       │
        │       ├─── Kobject? → Recurse with .dict()
        │       ├─── List/Tuple? → Map resolver over items
        │       ├─── Dict? → Map resolver over keys and values
        │       └─── Other? → Apply registered resolver
        │
        └─── Returns dict representation
                │
                ▼
        (to_json only) json.dumps() → bytes
```

### Deserialization Flow

```
Kobject.from_json(payload) / Kobject.from_dict(dict_repr)
        │
        ▼
For each field in _with_field_map():
        │
        ├─── Field missing and no default? → Add to _missing
        ├─── Field has value:
        │       │
        │       ▼
        │   JSONDecoder.type_caster(annotation, value)
        │       │
        │       ├─── Check registered resolvers
        │       └─── Apply matching resolver or return as-is
        │
        └─── Collection types:
                ├─── list → _resolve_list()
                ├─── tuple → _resolve_tuple()
                └─── dict → _resolve_dict()
        │
        ▼
cls(**resolved_dict) → Returns instance
```

## Resolver System

The resolver system allows custom type handling for encoding, decoding, and schema generation.

### Registration

```python
# Decoder: Deserialize custom types from JSON
Kobject.set_decoder_resolver(
    datetime,
    lambda attr_type, value: datetime.fromisoformat(value)
)

# Encoder: Serialize custom types to JSON
Kobject.set_encoder_resolver(
    datetime,
    lambda value: value.isoformat()
)

# Schema: Generate JSON Schema for custom types
Kobject.set_schema_resolver(
    datetime,
    lambda t: {"type": "string", "format": "date-time"}
)
```

### Resolution Order

1. **Exact type match**: Checks if the type exactly matches a registered resolver
2. **Subclass match**: Falls back to subclass checking for inheritance support

### Thread Safety

All resolver registration uses `threading.Lock` to ensure thread-safe access:

```python
class JSONDecoder:
    _lock: ClassVar[threading.Lock] = threading.Lock()
    types_resolver: ClassVar[list[tuple[type, Callable]]] = []

    @classmethod
    def register_resolver(cls, attr_type: type, callback: Callable) -> None:
        with cls._lock:
            cls.types_resolver.insert(0, (attr_type, callback))
```

## Field Map Caching

Field metadata is computed once per class and cached in a class variable:

```python
class Kobject:
    __field_map: ClassVar[dict[type[Any], list[FieldMeta]]] = {}

    @classmethod
    def _with_field_map(cls) -> list[FieldMeta]:
        if cls.__field_map.get(cls) is None:
            cls.__field_map[cls] = []
            for param in Signature.from_callable(cls).parameters.values():
                cls.__field_map[cls].append(FieldMeta.new_one(...))
        return cls.__field_map[cls]
```

This ensures:
- Each subclass has its own cached field list
- Signature inspection happens only once
- Subsequent instantiations reuse cached metadata

## JSON Schema Generation

The schema generator creates JSON Schema Draft 7 compatible output:

```python
User.json_schema()
# Returns:
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "title": "User Model",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    },
    "required": ["name", "age"],
    "additionalProperties": false
}
```

### Docstring Parsing

The generator extracts metadata from reST-style docstrings:

```python
class User(Kobject):
    """
    User Model

    Represents a system user.

    :param name: The user's full name
    :param age: Age in years
    :example: {"name": "Alice", "age": 30}
    """
```

This produces:
- `title`: "User Model"
- `description`: "Represents a system user."
- `properties.name.description`: "The user's full name"
- `examples`: [{"name": "Alice", "age": 30}]

### Nested Objects

Nested Kobject classes use `$ref` and `$defs` for schema composition:

```python
class Address(Kobject):
    street: str

class User(Kobject):
    address: Address

User.json_schema()
# Produces:
{
    "properties": {
        "address": {"$ref": "#/$defs/Address"}
    },
    "$defs": {
        "Address": {
            "type": "object",
            "properties": {"street": {"type": "string"}}
        }
    }
}
```

## Type Support

### Supported Types

| Category | Types |
|----------|-------|
| Primitives | `str`, `int`, `float`, `bool`, `None` |
| Collections | `list`, `tuple`, `dict`, `set` |
| Generics | `List[T]`, `Tuple[T, ...]`, `Dict[K, V]`, `Set[T]` |
| Union | `Union[A, B]`, `A \| B`, `Optional[T]` |
| Special | `Any`, `Callable`, `Coroutine` |
| Custom | `Enum`, `IntEnum`, Kobject subclasses |

### Default Resolvers

The `__init__.py` registers default resolvers for common types:

```python
# Primitives (identity)
Kobject.set_decoder_resolver(bool, lambda t, v: v)
Kobject.set_decoder_resolver(int, lambda t, v: v)
Kobject.set_decoder_resolver(str, lambda t, v: v)
Kobject.set_decoder_resolver(float, lambda t, v: v)

# Kobject subclasses (recursive deserialization)
Kobject.set_decoder_resolver(Kobject, lambda t, v: t.from_dict(v))

# Enums (value casting)
Kobject.set_decoder_resolver(Enum, lambda t, v: t(v))

# Schema types (datetime, UUID, Decimal)
Kobject.set_schema_resolver(datetime, lambda t: {"type": "string", "format": "date-time"})
Kobject.set_schema_resolver(UUID, lambda t: {"type": "string", "format": "uuid"})
Kobject.set_schema_resolver(Decimal, lambda t: {"type": "number"})
```

## Error Handling

Validation errors include structured information accessible via `json_error()`:

```python
try:
    User(name=123, age="old")
except TypeError as e:
    errors = e.json_error()
    # Returns:
    # [
    #     {"field": "name", "type": str, "value": "123"},
    #     {"field": "age", "type": int, "value": "'old'"}
    # ]
```

The `_enriched_error()` method dynamically attaches the `json_error()` method to exceptions using `types.MethodType`.

## Extension Points

1. **Custom Resolvers**: Register handlers for any type
2. **Custom Exceptions**: Override default TypeError with `set_validation_custom_exception()`
3. **Lazy Validation**: Stop at first error with `set_lazy_type_check(True)`
4. **Subclassing**: Extend Kobject for domain-specific behavior
