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

The library consists of two main files:

- **`kobject/__init__.py`**: Entry point that exports `Kobject` and `Empty`. Registers default decoder resolvers for primitive types (bool, float, int, str), Kobject subclasses, and Enums.

- **`kobject/validator.py`**: Core implementation containing:
  - `FieldMeta`: Dataclass representing a class field with pre-processed metadata (name, annotation, required, default value)
  - `Kobject`: Main base class users inherit from. Provides:
    - `__post_init__()`: Called after `__init__` to trigger validation (dataclasses call this automatically)
    - `_with_field_map()`: Caches and returns field metadata extracted from `__init__` signature
    - `from_json()`/`from_dict()`: Deserialize JSON/dict to class instance
    - `to_json()`/`dict()`: Serialize instance to JSON/dict
  - `JSONEncoder`/`JSONDecoder`: Handle custom type encoding/decoding via registered resolvers

## Key Patterns

**Type Validation Flow**: Validation happens in `__post_init__` → `__validate_model()` which iterates through `_with_field_map()` fields and calls `_validate_field_value()` for each.

**Supported Types**: Basic types, generics (List, Tuple, Dict), Union/Optional, Any, Callable, Coroutine, custom classes, and Enums.

**Resolver System**: Custom types can be serialized/deserialized by registering resolvers:
- `Kobject.set_decoder_resolver(type, lambda)` for deserialization
- `Kobject.set_encoder_resolver(type, lambda)` for serialization

**Default Class Usage**: Must explicitly call `self.__post_init__()` at the end of `__init__`.

**Test Structure**: Tests use pytest fixtures with `ClassType` enum to parameterize between dataclass and default class implementations.
