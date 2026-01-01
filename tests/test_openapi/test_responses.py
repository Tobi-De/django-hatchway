"""Tests for OpenAPI response generation."""

import pytest
from django.urls import path

from hatchway import Schema, api_view
from hatchway.openapi import OpenAPIConfig, OpenAPIGenerator


class UserSchema(Schema):
    """User schema."""

    id: int
    username: str
    email: str


class ErrorSchema(Schema):
    """Error schema."""

    message: str
    code: int


def test_success_response_with_schema():
    """Test that success responses include the output schema."""

    @api_view.get
    def get_user(request, user_id: int) -> UserSchema:
        """Get a user."""
        pass

    urlpatterns = [path("users/<int:user_id>/", get_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/{user_id}/"].get
    assert "200" in operation.responses

    response = operation.responses["200"]
    assert response.description == "Successful response"
    assert "application/json" in response.content

    media_type = response.content["application/json"]
    assert hasattr(media_type.schema, "ref")
    assert media_type.schema.ref == "#/components/schemas/UserSchema"


def test_success_response_without_schema():
    """Test success response when no output type is specified."""

    @api_view.get
    def health_check(request):
        """Health check."""
        return {"status": "ok"}

    urlpatterns = [path("health/", health_check)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/health/"].get
    assert "200" in operation.responses

    response = operation.responses["200"]
    assert response.description == "Successful response"


def test_post_returns_201():
    """Test that POST endpoints return 201 status code."""

    @api_view.post
    def create_user(request, data: UserSchema) -> UserSchema:
        """Create a user."""
        pass

    urlpatterns = [path("users/", create_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].post
    assert "201" in operation.responses
    assert "200" not in operation.responses  # POST should use 201, not 200


def test_get_returns_200():
    """Test that GET endpoints return 200 status code."""

    @api_view.get
    def list_users(request) -> list[UserSchema]:
        """List users."""
        return []

    urlpatterns = [path("users/", list_users)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].get
    assert "200" in operation.responses


def test_validation_error_response():
    """Test that all endpoints include 400 validation error response."""

    @api_view.post
    def create_user(request, data: UserSchema) -> UserSchema:
        """Create a user."""
        pass

    urlpatterns = [path("users/", create_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].post
    assert "400" in operation.responses

    error_response = operation.responses["400"]
    assert error_response.description == "Validation error"
    assert "application/json" in error_response.content

    schema = error_response.content["application/json"].schema
    assert schema.type == "object"
    assert "error" in schema.properties
    assert "error_details" in schema.properties


def test_auth_error_response():
    """Test that authenticated endpoints include 401 error response."""

    @api_view.get(auth=True)
    def protected_endpoint(request) -> dict:
        """Protected endpoint."""
        return {}

    urlpatterns = [path("protected/", protected_endpoint)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/protected/"].get
    assert "401" in operation.responses

    auth_error = operation.responses["401"]
    assert auth_error.description == "Authentication required"
    assert "application/json" in auth_error.content


def test_permission_error_response():
    """Test that endpoints with permissions include 403 error response."""

    @api_view.post(auth=True, permissions=["app.add_user"])
    def create_user(request, data: UserSchema) -> UserSchema:
        """Create a user."""
        pass

    urlpatterns = [path("users/", create_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].post
    assert "403" in operation.responses

    perm_error = operation.responses["403"]
    assert perm_error.description == "Permission denied"


def test_multiple_response_codes():
    """Test that endpoints can have multiple response codes."""

    @api_view.post(auth=True, permissions=["app.add_user"])
    def create_user(request, data: UserSchema) -> UserSchema:
        """Create a user."""
        pass

    urlpatterns = [path("users/", create_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].post

    # Should have success, validation, auth, and permission responses
    assert "201" in operation.responses  # Success
    assert "400" in operation.responses  # Validation
    assert "401" in operation.responses  # Auth
    assert "403" in operation.responses  # Permission


def test_list_response():
    """Test response with list type."""

    @api_view.get
    def list_users(request) -> list[UserSchema]:
        """List all users."""
        return []

    urlpatterns = [path("users/", list_users)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].get
    response = operation.responses["200"]

    media_type = response.content["application/json"]
    schema = media_type.schema

    # Should be an array type
    assert schema.type == "array"
    # items could be either a Reference or a dict with $ref
    if hasattr(schema.items, "ref"):
        assert schema.items.ref == "#/components/schemas/UserSchema"
    else:
        assert schema.items["$ref"] == "#/components/schemas/UserSchema"


def test_dict_response():
    """Test response with dict type."""

    @api_view.get
    def get_metadata(request) -> dict[str, str]:
        """Get metadata."""
        return {}

    urlpatterns = [path("metadata/", get_metadata)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/metadata/"].get
    response = operation.responses["200"]

    media_type = response.content["application/json"]
    schema = media_type.schema

    # Should be an object with additionalProperties
    assert schema.type == "object"
    assert schema.additional_properties is not None


def test_optional_response():
    """Test response with optional type."""

    @api_view.get
    def get_user(request, user_id: int) -> UserSchema | None:
        """Get a user (may be None)."""
        pass

    urlpatterns = [path("users/<int:user_id>/", get_user)]
    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/{user_id}/"].get
    response = operation.responses["200"]

    # The schema should handle nullable
    media_type = response.content["application/json"]
    assert media_type.schema is not None
