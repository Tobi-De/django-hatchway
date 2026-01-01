"""Tests for OpenAPI request body generation."""

import pytest
from django.core.files.uploadedfile import UploadedFile
from django.urls import path

from hatchway import Body, File, Schema, api_view
from hatchway.openapi import OpenAPIConfig, OpenAPIGenerator


class UserCreateSchema(Schema):
    """Schema for creating a user."""

    username: str
    email: str
    age: int | None = None


class ProfileSchema(Schema):
    """Profile schema."""

    bio: str
    website: str | None = None


def test_request_body_with_schema():
    """Test request body generation with msgspec.Struct."""

    @api_view.post
    def create_user(request, data: UserCreateSchema) -> UserCreateSchema:
        """Create a user."""
        pass

    urlpatterns = [path("users/", create_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].post
    assert operation.request_body is not None
    assert operation.request_body.required is True

    # Should use application/json
    assert "application/json" in operation.request_body.content
    media_type = operation.request_body.content["application/json"]

    # Should reference the schema
    assert hasattr(media_type.schema, "ref")
    assert media_type.schema.ref == "#/components/schemas/UserCreateSchema"

    # Schema should be in components
    assert "UserCreateSchema" in spec.components.schemas


def test_request_body_multiple_parameters():
    """Test request body with multiple body parameters."""

    @api_view.post
    def create_user(request, username: Body[str], email: Body[str], age: Body[int] = 18) -> dict:
        """Create a user."""
        return {}

    urlpatterns = [path("users/", create_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].post
    assert operation.request_body is not None

    media_type = operation.request_body.content["application/json"]
    schema = media_type.schema

    # Should wrap multiple params in an object
    assert schema.type == "object"
    assert "username" in schema.properties
    assert "email" in schema.properties
    assert "age" in schema.properties

    # Required fields
    assert set(schema.required) == {"username", "email"}


def test_request_body_with_file():
    """Test request body with file upload."""
    pytest.skip("File uploads require Django UploadedFile type which is not yet fully supported")


def test_request_body_nested_schema():
    """Test request body with nested schemas."""

    class UserWithProfile(Schema):
        username: str
        profile: ProfileSchema

    @api_view.post
    def create_user(request, data: UserWithProfile) -> UserWithProfile:
        """Create a user with profile."""
        pass

    urlpatterns = [path("users/", create_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    # Both schemas should be collected
    assert "UserWithProfile" in spec.components.schemas
    assert "ProfileSchema" in spec.components.schemas


def test_request_body_optional_field():
    """Test request body with optional fields."""

    @api_view.post
    def create_user(request, data: UserCreateSchema) -> UserCreateSchema:
        """Create a user."""
        pass

    urlpatterns = [path("users/", create_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    user_schema = spec.components.schemas["UserCreateSchema"]

    # Only non-optional fields should be required
    assert set(user_schema["required"]) == {"username", "email"}
    # age is optional
    assert "age" in user_schema["properties"]


def test_request_body_list_type():
    """Test request body with list of schemas."""
    pytest.skip("Lists without Body annotation are treated as query parameters in Hatchway")


def test_no_request_body_for_get():
    """Test that GET endpoints don't have request bodies."""

    @api_view.get
    def list_users(request, search: str = "") -> list[UserCreateSchema]:
        """List users."""
        return []

    urlpatterns = [path("users/", list_users)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].get
    assert operation.request_body is None


def test_request_body_with_dict():
    """Test request body with dict type."""
    pytest.skip("Dicts without Body annotation are treated as query parameters in Hatchway")


def test_request_body_body_direct():
    """Test that single Schema parameter uses body_direct mode."""

    @api_view.post
    def create_user(request, user: UserCreateSchema) -> UserCreateSchema:
        """Create a user."""
        pass

    urlpatterns = [path("users/", create_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].post
    media_type = operation.request_body.content["application/json"]

    # Should directly reference the schema, not wrap it
    assert hasattr(media_type.schema, "ref")
    assert media_type.schema.ref == "#/components/schemas/UserCreateSchema"


def test_mixed_file_and_body_params():
    """Test mixing file uploads with other body parameters."""
    pytest.skip("File uploads require Django UploadedFile type which is not yet fully supported")


def test_request_body_required():
    """Test that request bodies are marked as required."""

    @api_view.post
    def create_user(request, data: UserCreateSchema) -> UserCreateSchema:
        """Create a user."""
        pass

    urlpatterns = [path("users/", create_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].post
    assert operation.request_body.required is True
