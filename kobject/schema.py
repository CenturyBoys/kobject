"""JSON Schema generation for Kobject classes."""

from __future__ import annotations

import contextlib
import json
import re
import threading
import types
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from inspect import isclass
from typing import Any, ClassVar, Union, get_args, get_origin

# Type alias for schema resolver callback
SchemaResolverCallback = Callable[[type[Any]], dict[str, Any]]


@dataclass(slots=True, frozen=True)
class DocstringMeta:
    """Parsed metadata from a class docstring."""

    title: str | None = None
    description: str | None = None
    field_descriptions: dict[str, str] = field(default_factory=dict)
    examples: list[dict[str, Any]] = field(default_factory=list)


def parse_docstring(docstring: str | None) -> DocstringMeta:
    """
    Parse a reST-style docstring into metadata.

    Extracts:
    - title: First non-empty line
    - description: Text between title and first directive
    - field_descriptions: :param field_name: descriptions
    - examples: :example: JSON objects
    """
    if not docstring:
        return DocstringMeta()

    lines = docstring.strip().split("\n")
    if not lines:
        return DocstringMeta()

    title: str | None = None
    description_lines: list[str] = []
    field_descriptions: dict[str, str] = {}
    examples: list[dict[str, Any]] = []

    # Find title (first non-empty line)
    line_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            title = stripped
            line_idx = i + 1
            break

    # Parse remaining lines
    in_description = True
    current_param: str | None = None
    current_param_lines: list[str] = []

    param_pattern = re.compile(r":param\s+(\w+):\s*(.*)")
    example_pattern = re.compile(r":example:\s*(.*)")

    def flush_param() -> None:
        nonlocal current_param, current_param_lines
        if current_param and current_param_lines:
            field_descriptions[current_param] = " ".join(current_param_lines).strip()
        current_param = None
        current_param_lines = []

    for line in lines[line_idx:]:
        stripped = line.strip()

        # Check for :param field: description
        param_match = param_pattern.match(stripped)
        if param_match:
            flush_param()
            in_description = False
            current_param = param_match.group(1)
            param_text = param_match.group(2).strip()
            if param_text:
                current_param_lines.append(param_text)
            continue

        # Check for :example: {...}
        example_match = example_pattern.match(stripped)
        if example_match:
            flush_param()
            in_description = False
            example_text = example_match.group(1).strip()
            if example_text:
                with contextlib.suppress(json.JSONDecodeError):
                    examples.append(json.loads(example_text))
            continue

        # Check for other directives (stop description)
        if stripped.startswith(":"):
            flush_param()
            in_description = False
            continue

        # Continuation of current param
        if current_param is not None and stripped:
            current_param_lines.append(stripped)
            continue

        # Description lines (before any directive)
        if in_description and stripped:
            description_lines.append(stripped)

    flush_param()

    description: str | None = None
    if description_lines:
        description = " ".join(description_lines)

    return DocstringMeta(
        title=title,
        description=description,
        field_descriptions=field_descriptions,
        examples=examples,
    )


def _is_union(attr_type: type | type[Any]) -> bool:
    """Check if attr_type is a Union type."""
    return get_origin(attr_type) is Union or isinstance(attr_type, types.UnionType)


def _is_optional(attr_type: type[Any]) -> tuple[bool, type[Any] | None]:
    """
    Check if a type is Optional (T | None).

    Returns (is_optional, inner_type) where inner_type is the non-None type.
    """
    if not _is_union(attr_type):
        return False, None

    args = get_args(attr_type)
    non_none_types = [t for t in args if t is not type(None)]

    if len(non_none_types) == len(args):
        # No None in the union
        return False, None

    if len(non_none_types) == 1:
        return True, non_none_types[0]

    # Multiple non-None types with None (e.g., str | int | None)
    return True, None


class JSONSchemaGenerator:
    """
    Generates JSON Schema Draft 7 from Kobject classes.

    Supports custom type resolvers via register_resolver().
    """

    _lock: ClassVar[threading.Lock] = threading.Lock()
    schema_resolvers: ClassVar[list[tuple[type, SchemaResolverCallback]]] = []

    @classmethod
    def register_resolver(
        cls, attr_type: type, callback: SchemaResolverCallback
    ) -> None:
        """
        Register a schema resolver for a type.

        Args:
            attr_type: The type to match (supports subclass matching)
            callback: Function that returns JSON Schema dict for the type
        """
        with cls._lock:
            cls.schema_resolvers.insert(0, (attr_type, callback))

    @classmethod
    def get_schema_for_type(
        cls,
        attr_type: type[Any],
        defs: dict[str, dict[str, Any]],
        processed: set[type],
    ) -> dict[str, Any]:
        """
        Get JSON Schema for a Python type.

        Args:
            attr_type: The Python type to convert
            defs: Dictionary to accumulate $defs for nested Kobjects
            processed: Set of types already processed (cycle detection)

        Returns:
            JSON Schema dict for the type
        """
        # Import here to avoid circular imports
        from kobject.core import Kobject

        # Check custom resolvers first (exact match takes priority)
        if isclass(attr_type):
            # First pass: exact type match
            for resolver_type, resolver in cls.schema_resolvers:
                if attr_type is resolver_type:
                    return resolver(attr_type)
            # Second pass: subclass match
            for resolver_type, resolver in cls.schema_resolvers:
                if issubclass(attr_type, resolver_type):
                    return resolver(attr_type)

        # Handle None type
        if attr_type is type(None):
            return {"type": "null"}

        # Handle basic types
        if attr_type is str:
            return {"type": "string"}
        if attr_type is int:
            return {"type": "integer"}
        if attr_type is float:
            return {"type": "number"}
        if attr_type is bool:
            return {"type": "boolean"}

        # Handle bare collection types (list, dict, tuple, set without type args)
        if attr_type is list:
            return {"type": "array"}
        if attr_type is dict:
            return {"type": "object"}
        if attr_type is tuple:
            return {"type": "array"}
        if attr_type is set:
            return {"type": "array", "uniqueItems": True}

        # Handle Any
        if attr_type is Any:
            return {}

        # Handle Enum
        if isclass(attr_type) and issubclass(attr_type, Enum):
            values = [e.value for e in attr_type]
            if issubclass(attr_type, IntEnum):
                return {"type": "integer", "enum": values}
            if all(isinstance(v, str) for v in values):
                return {"type": "string", "enum": values}
            return {"enum": values}

        # Handle Kobject subclass
        if (
            isclass(attr_type)
            and issubclass(attr_type, Kobject)
            and attr_type is not Kobject
        ):
            class_name = attr_type.__name__
            if attr_type not in processed:
                processed.add(attr_type)
                nested_schema = cls._generate_object_schema(attr_type, defs, processed)
                defs[class_name] = nested_schema
            return {"$ref": f"#/$defs/{class_name}"}

        # Handle generic types
        origin = get_origin(attr_type)
        args = get_args(attr_type)

        # Handle Union types
        if _is_union(attr_type):
            is_opt, inner_type = _is_optional(attr_type)
            if is_opt and inner_type is not None:
                # Simple Optional[T] -> anyOf with null
                inner_schema = cls.get_schema_for_type(inner_type, defs, processed)
                return {"anyOf": [inner_schema, {"type": "null"}]}
            # Complex union
            schemas = [cls.get_schema_for_type(t, defs, processed) for t in args]
            return {"anyOf": schemas}

        # Handle list
        if origin is list:
            if args:
                items_schema = cls.get_schema_for_type(args[0], defs, processed)
                return {"type": "array", "items": items_schema}
            return {"type": "array"}

        # Handle tuple
        if origin is tuple:
            if args:
                # Check for variable-length tuple (T, ...)
                if len(args) == 2 and args[1] is ...:
                    items_schema = cls.get_schema_for_type(args[0], defs, processed)
                    return {"type": "array", "items": items_schema}
                # Fixed-length tuple
                prefix_items = [
                    cls.get_schema_for_type(t, defs, processed) for t in args
                ]
                return {
                    "type": "array",
                    "prefixItems": prefix_items,
                    "minItems": len(args),
                    "maxItems": len(args),
                }
            return {"type": "array"}

        # Handle dict
        if origin is dict:
            if args and len(args) >= 2:
                value_schema = cls.get_schema_for_type(args[1], defs, processed)
                return {"type": "object", "additionalProperties": value_schema}
            return {"type": "object"}

        # Handle set
        if origin is set:
            if args:
                items_schema = cls.get_schema_for_type(args[0], defs, processed)
                return {"type": "array", "items": items_schema, "uniqueItems": True}
            return {"type": "array", "uniqueItems": True}

        # Fallback for unknown types
        return {}

    @classmethod
    def _generate_object_schema(
        cls,
        klass: type,
        defs: dict[str, dict[str, Any]],
        processed: set[type],
    ) -> dict[str, Any]:
        """Generate the object schema for a Kobject class (without $defs)."""
        from kobject.core import Kobject

        if not issubclass(klass, Kobject):
            return {}

        docstring_meta = parse_docstring(klass.__doc__)
        fields = klass._with_field_map()

        properties: dict[str, Any] = {}
        required: list[str] = []

        for fld in fields:
            prop_schema = cls.get_schema_for_type(fld.annotation, defs, processed)

            # Add field description from docstring
            if fld.name in docstring_meta.field_descriptions:
                prop_schema["description"] = docstring_meta.field_descriptions[fld.name]

            # Add default value if present
            if fld.have_default_value:
                # Only add serializable defaults
                default_val = fld.default
                if isinstance(
                    default_val, str | int | float | bool | type(None) | list | dict
                ):
                    prop_schema["default"] = default_val
            else:
                required.append(fld.name)

            properties[fld.name] = prop_schema

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
        }

        if required:
            schema["required"] = required

        return schema

    @classmethod
    def generate(cls, klass: type) -> dict[str, Any]:
        """
        Generate JSON Schema Draft 7 for a Kobject class.

        Args:
            klass: The Kobject class to generate schema for

        Returns:
            Complete JSON Schema dict with $schema, title, etc.
        """
        from kobject.core import Kobject

        if not issubclass(klass, Kobject):
            raise TypeError(f"{klass.__name__} is not a Kobject subclass")

        defs: dict[str, dict[str, Any]] = {}
        processed: set[type] = {klass}

        # Parse docstring for metadata
        docstring_meta = parse_docstring(klass.__doc__)
        fields = klass._with_field_map()

        properties: dict[str, Any] = {}
        required: list[str] = []

        for fld in fields:
            prop_schema = cls.get_schema_for_type(fld.annotation, defs, processed)

            # Add field description from docstring
            if fld.name in docstring_meta.field_descriptions:
                prop_schema["description"] = docstring_meta.field_descriptions[fld.name]

            # Add default value if present
            if fld.have_default_value:
                default_val = fld.default
                if isinstance(
                    default_val, str | int | float | bool | type(None) | list | dict
                ):
                    prop_schema["default"] = default_val
            else:
                required.append(fld.name)

            properties[fld.name] = prop_schema

        schema: dict[str, Any] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
        }

        # Add title from docstring
        if docstring_meta.title:
            schema["title"] = docstring_meta.title

        # Add description if different from title
        if (
            docstring_meta.description
            and docstring_meta.description != docstring_meta.title
        ):
            schema["description"] = docstring_meta.description

        if required:
            schema["required"] = required

        # Add examples from docstring
        if docstring_meta.examples:
            schema["examples"] = docstring_meta.examples

        # Add $defs if there are nested Kobject references
        if defs:
            schema["$defs"] = defs

        return schema
