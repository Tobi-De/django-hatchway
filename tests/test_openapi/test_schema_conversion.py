"""Tests for msgspec.Struct to OpenAPI schema conversion."""

from typing import Annotated

import msgspec
import pytest

from hatchway import Meta, Schema
from hatchway.openapi.schema import (
    collect_schema_definitions,
    get_openapi_type,
    struct_to_schema,
)


def test_basic_types():
    """Test OpenAPI type conversion for basic Python types."""
    assert get_openapi_type(int) == {"type": "integer"}
    assert get_openapi_type(str) == {"type": "string"}
    assert get_openapi_type(float) == {"type": "number", "format": "double"}
    assert get_openapi_type(bool) == {"type": "boolean"}


def test_optional_types():
    """Test OpenAPI type conversion for Optional types."""
    schema = get_openapi_type(int | None)
    assert schema["type"] == "integer"
    assert schema["nullable"] is True

    schema = get_openapi_type(str | None)
    assert schema["type"] == "string"
    assert schema["nullable"] is True


def test_list_types():
    """Test OpenAPI type conversion for list types."""
    schema = get_openapi_type(list[str])
    assert schema["type"] == "array"
    assert schema["items"]["type"] == "string"

    schema = get_openapi_type(list[int])
    assert schema["type"] == "array"
    assert schema["items"]["type"] == "integer"


def test_dict_types():
    """Test OpenAPI type conversion for dict types."""
    schema = get_openapi_type(dict[str, int])
    assert schema["type"] == "object"
    assert schema["additionalProperties"]["type"] == "integer"

    schema = get_openapi_type(dict[str, str])
    assert schema["type"] == "object"
    assert schema["additionalProperties"]["type"] == "string"


def test_struct_reference():
    """Test that msgspec.Struct types produce $ref references."""

    class Person(Schema):
        name: str
        age: int

    schema = get_openapi_type(Person)
    assert "$ref" in schema
    assert schema["$ref"] == "#/components/schemas/Person"


def test_struct_to_schema_basic():
    """Test basic msgspec.Struct to OpenAPI schema conversion."""

    class User(Schema):
        """A user model."""

        username: str
        email: str
        age: int

    schema = struct_to_schema(User)

    assert schema["type"] == "object"
    assert schema["description"] == "A user model."
    assert "properties" in schema
    assert "required" in schema

    # Check properties
    props = schema["properties"]
    assert props["username"]["type"] == "string"
    assert props["email"]["type"] == "string"
    assert props["age"]["type"] == "integer"

    # Check required fields
    assert set(schema["required"]) == {"username", "email", "age"}


def test_struct_to_schema_optional_fields():
    """Test schema conversion with optional fields."""

    class User(Schema):
        username: str
        email: str
        bio: str | None = None
        age: int | None = None

    schema = struct_to_schema(User)

    # Only non-optional fields should be required
    assert set(schema["required"]) == {"username", "email"}

    # Optional fields should still be in properties
    props = schema["properties"]
    assert "bio" in props
    assert "age" in props
    assert props["bio"]["nullable"] is True
    assert props["age"]["nullable"] is True


def test_struct_with_constraints():
    """Test schema conversion with msgspec validation constraints."""

    class Product(Schema):
        name: Annotated[str, Meta(min_length=3, max_length=100)]
        price: Annotated[float, Meta(gt=0)]
        quantity: Annotated[int, Meta(ge=0, le=1000)]

    schema = struct_to_schema(Product)
    props = schema["properties"]

    # Check string constraints
    assert props["name"]["minLength"] == 3
    assert props["name"]["maxLength"] == 100

    # Check number constraints
    assert props["price"]["minimum"] == 0
    assert props["price"]["exclusiveMinimum"] is True

    # Check integer constraints
    assert props["quantity"]["minimum"] == 0
    assert props["quantity"]["maximum"] == 1000


def test_nested_structs():
    """Test schema conversion with nested struct types."""

    class Address(Schema):
        street: str
        city: str
        zipcode: str

    class Person(Schema):
        name: str
        address: Address

    schema = struct_to_schema(Person)
    props = schema["properties"]

    # Nested struct should be a reference
    assert "$ref" in props["address"]
    assert props["address"]["$ref"] == "#/components/schemas/Address"


def test_collect_schema_definitions_simple():
    """Test collecting schema definitions from a simple struct."""

    class User(Schema):
        username: str
        email: str

    definitions = collect_schema_definitions(User)

    assert "User" in definitions
    assert definitions["User"]["type"] == "object"
    assert "username" in definitions["User"]["properties"]


def test_collect_schema_definitions_nested():
    """Test collecting nested schema definitions."""

    class Address(Schema):
        street: str
        city: str

    class Person(Schema):
        name: str
        address: Address

    definitions = collect_schema_definitions(Person)

    # Both schemas should be collected
    assert "Person" in definitions
    assert "Address" in definitions

    # Person should reference Address
    assert definitions["Person"]["properties"]["address"]["$ref"] == "#/components/schemas/Address"


def test_collect_schema_definitions_list():
    """Test collecting schemas from list types."""

    class Tag(Schema):
        name: str

    class Post(Schema):
        title: str
        tags: list[Tag]

    definitions = collect_schema_definitions(Post)

    # Both schemas should be collected
    assert "Post" in definitions
    assert "Tag" in definitions


def test_collect_schema_definitions_optional():
    """Test collecting schemas from optional types."""

    class Profile(Schema):
        bio: str

    class User(Schema):
        username: str
        profile: Profile | None = None

    definitions = collect_schema_definitions(User)

    # Both schemas should be collected even though Profile is optional
    assert "User" in definitions
    assert "Profile" in definitions


def test_datetime_types():
    """Test OpenAPI type conversion for datetime types."""
    from datetime import date, datetime

    schema = get_openapi_type(datetime)
    assert schema["type"] == "string"
    assert schema["format"] == "date-time"

    schema = get_openapi_type(date)
    assert schema["type"] == "string"
    assert schema["format"] == "date"


def test_bytes_type():
    """Test OpenAPI type conversion for bytes type."""
    schema = get_openapi_type(bytes)
    assert schema["type"] == "string"
    assert schema["format"] == "binary"


def test_list_with_nested_struct():
    """Test list containing nested structs."""

    class Item(Schema):
        id: int
        name: str

    schema = get_openapi_type(list[Item])
    assert schema["type"] == "array"
    assert schema["items"]["$ref"] == "#/components/schemas/Item"


def test_complex_nested_structure():
    """Test complex nested structure with multiple levels."""

    class Tag(Schema):
        name: str
        color: str

    class Comment(Schema):
        text: str
        author: str

    class Post(Schema):
        title: str
        content: str
        tags: list[Tag]
        comments: list[Comment] | None = None

    definitions = collect_schema_definitions(Post)

    # All schemas should be collected
    assert "Post" in definitions
    assert "Tag" in definitions
    assert "Comment" in definitions

    # Verify structure
    post_schema = definitions["Post"]
    assert post_schema["properties"]["tags"]["type"] == "array"
    assert post_schema["properties"]["tags"]["items"]["$ref"] == "#/components/schemas/Tag"
