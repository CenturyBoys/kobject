# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kobject is a Python `__init__` type validator for classes and dataclasses. It validates attribute types at instantiation time by inspecting the `__init__` signature, supporting both standard classes and dataclasses with Python 3.10+.

## Commands

```bash
# Install dependencies
poetry install

# Run tests
pytest

# Run a single test file
pytest tests/kobject/validator/test_main.py

# Run a specific test
pytest tests/kobject/validator/test_main.py::test_simple_attr -v

# Lint and format (via pre-commit)
ruff check --fix .
ruff format .

# Run mutation testing (used in pre-commit)
mutatest -n 100 -s kobject
```

## Architecture

The library is organized into the following modules:

- **`kobject/__init__.py`**: Entry point that exports `Kobject`, `Empty`, and `JSONSchemaGenerator`. Registers default resolvers for primitive types, Kobject subclasses, Enums, and schema types (datetime, UUID, Decimal).

- **`kobject/core.py`**: Main `Kobject` base class that users inherit from. Provides:
  - `__post_init__()`: Called after `__init__` to trigger validation
  - `_with_field_map()`: Caches and returns field metadata from `__init__` signature
  - `from_json()`/`from_dict()`: Deserialize JSON/dict to class instance
  - `to_json()`/`dict()`: Serialize instance to JSON/dict
  - `json_schema()`: Generate JSON Schema Draft 7 for the class
  - `set_decoder_resolver()`/`set_encoder_resolver()`/`set_schema_resolver()`: Register custom resolvers

- **`kobject/fields.py`**: `FieldMeta` dataclass representing a class field with pre-processed metadata (name, annotation, required, default value).

- **`kobject/serialization.py`**: `JSONEncoder`/`JSONDecoder` classes that handle custom type encoding/decoding via registered resolvers.

- **`kobject/validation.py`**: Type validation logic used by `__post_init__`.

- **`kobject/schema.py`**: JSON Schema generation containing:
  - `DocstringMeta`: Dataclass for parsed docstring metadata (title, description, field descriptions, examples)
  - `parse_docstring()`: Extracts metadata from reST-style docstrings
  - `JSONSchemaGenerator`: Generates JSON Schema Draft 7 with support for custom type resolvers

## Key Patterns

**Type Validation Flow**: Validation happens in `__post_init__` → `__validate_model()` which iterates through `_with_field_map()` fields and calls `_validate_field_value()` for each.

**Supported Types**: Basic types, generics (List, Tuple, Dict, Set), Union/Optional, Any, Callable, Coroutine, custom classes, and Enums.

**Resolver System**: Custom types can be handled by registering resolvers:
- `Kobject.set_decoder_resolver(type, lambda)` for deserialization
- `Kobject.set_encoder_resolver(type, lambda)` for serialization
- `Kobject.set_schema_resolver(type, lambda)` for JSON Schema generation

**JSON Schema Generation**: The `json_schema()` method generates JSON Schema Draft 7 from class definitions. It extracts metadata from reST-style docstrings (`:param:`, `:example:`) and handles nested Kobjects via `$ref`/`$defs`.

**Default Class Usage**: Must explicitly call `self.__post_init__()` at the end of `__init__`.

**Test Structure**: Tests use pytest fixtures with `ClassType` enum to parameterize between dataclass and default class implementations.
