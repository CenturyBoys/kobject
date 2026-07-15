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

# Lint, format, type-check (mirrors the CI `lint` job)
ruff check .
ruff format --check .
mypy kobject/

# Run all pre-commit hooks (ruff --fix, ruff-format, pytest)
pre-commit run --all-files

# Mutation testing (standalone; not part of pre-commit or CI)
mutatest -n 100 -s kobject
```

CI (`.github/workflows/ci.yml`) runs the lint job (ruff check, ruff format --check, mypy) plus a test matrix across Python 3.10/3.11/3.12. `pyproject.toml` enforces strict mypy (`disallow_untyped_defs`) and a broad ruff rule set (`E,F,W,I,UP,B,C4,SIM,RUF`).

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
  - `set_lazy_type_check()`, `set_validation_custom_exception()`, `set_content_check_custom_exception()`: Class-level config toggles (all mutate class state — see the resolver-state caveat below)

- **`kobject/_compat.py`**: Compatibility helpers that avoid importing private Python internals — `is_generic_alias()`, `is_special_form_union()` (Union/Optional/`X | Y`), and the `EMPTY` sentinel. Use these instead of touching `typing`/`types` internals directly.

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

**Global Resolver State**: Resolvers and config toggles live on class-level containers (`JSONDecoder.types_resolver`, `JSONEncoder.base_types_resolver`, `JSONSchemaGenerator.schema_resolvers`, and `Kobject`'s config flags). They persist across the process, so registering one in a test leaks into others. `tests/conftest.py` provides two autouse fixtures (`reset_resolvers`, `reset_kobject_config`) that snapshot and restore this state around every test — rely on them rather than manually cleaning up.

**Test Structure**: Tests use pytest fixtures with a `ClassType` enum (see `tests/kobject/validator/test_main.py`) to parameterize each case across both dataclass and default-class implementations, so validation behavior is verified identically for both. Tests are grouped by feature area under `tests/kobject/` (`validator/`, `schema/`, `from_json/`, `to_json/`, `field_metadata/`).
