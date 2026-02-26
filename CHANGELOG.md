# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.1] - 2026-02

### Added
- `ARCHITECTURE.md` with comprehensive architecture documentation and flow diagrams
- `CHANGELOG.md` following Keep a Changelog format (retroactive)
- GitHub Actions CI/CD workflows:
  - `ci.yml` for lint, type check, and test matrix (Python 3.10, 3.11, 3.12)
  - `publish.yml` for automated PyPI publishing on releases
- Sphinx documentation configuration in `docs/`
- Additional tests for Union type validation in collections (13 new tests)

### Changed
- Extracted `_build_properties_and_required()` method in `schema.py` to eliminate code duplication
- Improved type hints with `TYPE_CHECKING` imports for better static analysis

### Fixed
- All MyPy errors resolved (15 → 0):
  - Added `bound="Kobject"` to TypeVar T
  - Fixed exception type narrowing with `or TypeError`
  - Added `_Dict` alias to avoid method shadowing by `dict()`
  - Fixed parameter type in `_resolve_dict()` to `dict[Any, Any]`
- Removed unused `is_union_type()` function from `_compat.py`
- Improved test coverage:
  - `validation.py`: 86% → 88%
  - `_compat.py`: 79% → 90%

## [0.7.0] - 2026-02

### Added
- `json_schema()` method for JSON Schema Draft 7 generation
- JSON Schema support for nested Kobjects via `$ref`/`$defs`
- Docstring parsing for schema metadata (`:param:`, `:example:`)
- `set_schema_resolver()` for custom type schema generation
- Default schema resolvers for `datetime`, `UUID`, and `Decimal`
- `remove_nones` parameter to `dict()` and `to_json()` methods
- `json_error()` method on exceptions for structured validation errors

### Changed
- Split `validator.py` into separate modules for better organization:
  - `core.py` - Main Kobject class
  - `validation.py` - Type validation logic
  - `serialization.py` - JSON encoder/decoder
  - `schema.py` - JSON Schema generation
  - `fields.py` - Field metadata
- Added thread safety with `threading.Lock` for resolver registration

### Fixed
- Do not cast explicit `None` values during deserialization
- `Empty` class now has proper `__bool__` implementation

## [0.6.1] - 2024-02

### Added
- Support for dict values in `from_json` partial usage

## [0.6.0] - 2024-01

### Changed
- Modified behavior of `dict()` method to allow resolving with encoder or not, to better fit use cases

## [0.5.4] - 2023-11

### Fixed
- Split tuple and list validation for proper length checking
- Improved sentinel usage to eliminate mutation testing survivors

## [0.5.3] - 2023-11

### Fixed
- Inheritance tree handling for nested class hierarchies
- Removed whitespace in JSON output

## [0.5.2] - 2023-11

### Fixed
- Default value detection for fields with defaults

## [0.5.1] - 2023-11

### Fixed
- Enum casting during deserialization
- Missing logic in `from_json` for enum handling

## [0.5.0] - 2023-05

### Added
- Mutation testing with `mutatest` for test quality
- Lazy type checking mode (stop at first error)
- Performance optimizations with field map caching

### Changed
- Refactored validation logic for better performance

## [0.4.0] - 2023-04

### Added
- Support for `dict` attributes with typed keys and values
- `Dict[K, V]` type validation

## [0.3.12] - 2023-03

### Fixed
- Validation of Kobject class attributes in `from_json`

## [0.3.11] - 2023-03

### Fixed
- Exception handling for invalid JSON content in `from_json`

## [0.3.10] - 2023-03

### Fixed
- Enum casting during `from_json` deserialization

## [0.3.9] - 2023-02

### Fixed
- Iterable validation for nested collections

## [0.3.8] - 2023-02

### Fixed
- Float casting and value caster improvements

## [0.3.7] - 2023-02

### Fixed
- Initial stability improvements

[0.7.1]: https://github.com/CenturyBoys/kobject/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/CenturyBoys/kobject/compare/v0.6.1...v0.7.0
[0.6.1]: https://github.com/CenturyBoys/kobject/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/CenturyBoys/kobject/compare/v0.5.4...v0.6.0
[0.5.4]: https://github.com/CenturyBoys/kobject/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/CenturyBoys/kobject/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/CenturyBoys/kobject/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/CenturyBoys/kobject/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/CenturyBoys/kobject/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/CenturyBoys/kobject/compare/v0.3.12...v0.4.0
[0.3.12]: https://github.com/CenturyBoys/kobject/compare/v0.3.11...v0.3.12
[0.3.11]: https://github.com/CenturyBoys/kobject/compare/v0.3.10...v0.3.11
[0.3.10]: https://github.com/CenturyBoys/kobject/compare/v0.3.9...v0.3.10
[0.3.9]: https://github.com/CenturyBoys/kobject/compare/v0.3.8...v0.3.9
[0.3.8]: https://github.com/CenturyBoys/kobject/compare/v0.3.7...v0.3.8
[0.3.7]: https://github.com/CenturyBoys/kobject/releases/tag/v0.3.7
