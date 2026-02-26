"""Pytest configuration and fixtures for kobject tests."""

import pytest

from kobject import Kobject
from kobject.schema import JSONSchemaGenerator
from kobject.serialization import JSONDecoder, JSONEncoder


@pytest.fixture(autouse=True)
def reset_resolvers():
    """Reset global resolver state before each test."""
    original_decoders = JSONDecoder.types_resolver.copy()
    original_encoders = JSONEncoder.base_types_resolver.copy()
    original_schema_resolvers = JSONSchemaGenerator.schema_resolvers.copy()
    yield
    JSONDecoder.types_resolver[:] = original_decoders
    JSONEncoder.base_types_resolver.clear()
    JSONEncoder.base_types_resolver.update(original_encoders)
    JSONSchemaGenerator.schema_resolvers[:] = original_schema_resolvers


@pytest.fixture(autouse=True)
def reset_kobject_config():
    """Reset Kobject class configuration."""
    Kobject.set_validation_custom_exception(None)
    Kobject.set_lazy_type_check(False)
    Kobject.set_content_check_custom_exception(None)
    yield
    Kobject.set_validation_custom_exception(None)
    Kobject.set_lazy_type_check(False)
    Kobject.set_content_check_custom_exception(None)
