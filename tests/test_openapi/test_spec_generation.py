"""Tests for OpenAPI specification generation from Hatchway views."""

import pytest
from django.urls import path

from hatchway import ApiError, Schema, api_view
from hatchway.openapi import OpenAPIConfig, OpenAPIGenerator


class UserSchema(Schema):
    """User model schema."""

    username: str
    email: str
    age: int | None = None


class PostSchema(Schema):
    """Blog post schema."""

    title: str
    content: str
    author: UserSchema


def test_basic_get_endpoint():
    """Test OpenAPI generation for a simple GET endpoint."""

    @api_view.get
    def health_check(request) -> dict:
        """Health check endpoint."""
        return {"status": "ok"}

    urlpatterns = [path("health/", health_check)]

    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    # Verify basic spec structure
    assert spec.openapi == "3.0.3"
    assert spec.info.title == "Test API"
    assert spec.info.version == "1.0.0"

    # Verify path exists
    assert "/health/" in spec.paths
    path_item = spec.paths["/health/"]
    assert path_item.get is not None

    # Verify operation
    operation = path_item.get
    assert operation.summary == "Health check endpoint."
    assert operation.operation_id == "health_check"


def test_path_parameters():
    """Test OpenAPI generation for endpoints with path parameters."""

    @api_view.get
    def get_user(request, user_id: int) -> UserSchema:
        """Get user by ID."""
        raise ApiError(404, "Not implemented")

    urlpatterns = [path("users/<int:user_id>/", get_user)]

    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    # Verify path parameter extraction
    assert "/users/{user_id}/" in spec.paths
    operation = spec.paths["/users/{user_id}/"].get

    # Check parameters
    assert operation.parameters is not None
    assert len(operation.parameters) == 1
    param = operation.parameters[0]
    assert param.name == "user_id"
    assert param.param_in == "path"
    assert param.required is True
    assert param.schema.type == "integer"


def test_query_parameters():
    """Test OpenAPI generation for endpoints with query parameters."""

    @api_view.get
    def list_users(request, limit: int = 10, offset: int = 0, search: str = None) -> list[UserSchema]:
        """List users with pagination."""
        return []

    urlpatterns = [path("users/", list_users)]

    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].get
    assert operation.parameters is not None

    # Group parameters by name for easier checking
    params_by_name = {p.name: p for p in operation.parameters}

    # Check limit parameter
    assert "limit" in params_by_name
    assert params_by_name["limit"].param_in == "query"
    assert params_by_name["limit"].required is False
    assert params_by_name["limit"].schema.default == 10

    # Check offset parameter
    assert "offset" in params_by_name
    assert params_by_name["offset"].schema.default == 0

    # Check search parameter
    assert "search" in params_by_name
    assert params_by_name["search"].required is False


def test_request_body():
    """Test OpenAPI generation for POST endpoint with request body."""

    @api_view.post
    def create_user(request, data: UserSchema) -> UserSchema:
        """Create a new user."""
        raise ApiError(400, "Not implemented")

    urlpatterns = [path("users/", create_user)]

    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/users/"].post

    # Check request body
    assert operation.request_body is not None
    assert operation.request_body.required is True
    assert "application/json" in operation.request_body.content

    # Check schema reference
    media_type = operation.request_body.content["application/json"]
    assert hasattr(media_type.schema, "ref")
    assert media_type.schema.ref == "#/components/schemas/UserSchema"

    # Check that schema definition was collected
    assert spec.components is not None
    assert "UserSchema" in spec.components.schemas


def test_response_schema():
    """Test OpenAPI generation for endpoint with response schema."""

    @api_view.get
    def get_post(request, post_id: int) -> PostSchema:
        """Get a blog post."""
        raise ApiError(404, "Not found")

    urlpatterns = [path("posts/<int:post_id>/", get_post)]

    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/posts/{post_id}/"].get

    # Check response
    assert "200" in operation.responses
    response = operation.responses["200"]
    assert "application/json" in response.content

    # Check schema reference
    media_type = response.content["application/json"]
    assert hasattr(media_type.schema, "ref")
    assert media_type.schema.ref == "#/components/schemas/PostSchema"

    # Check nested schema collection
    assert spec.components is not None
    assert "PostSchema" in spec.components.schemas
    assert "UserSchema" in spec.components.schemas  # Nested schema


def test_authentication():
    """Test OpenAPI generation for authenticated endpoints."""

    @api_view.get(auth=True)
    def protected_endpoint(request) -> dict:
        """Protected endpoint."""
        return {"secret": "data"}

    urlpatterns = [path("protected/", protected_endpoint)]

    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    operation = spec.paths["/protected/"].get

    # Check security requirements
    assert operation.security is not None
    assert len(operation.security) > 0
    assert {"TokenAuth": []} in operation.security or {"SessionAuth": []} in operation.security

    # Check security schemes in components
    assert spec.components is not None
    assert spec.components.security_schemes is not None
    assert "TokenAuth" in spec.components.security_schemes
    assert "SessionAuth" in spec.components.security_schemes


def test_multiple_methods():
    """Test OpenAPI generation for endpoint with multiple HTTP methods."""
    from hatchway.urls import methods

    @api_view.get
    def get_users(request) -> list[UserSchema]:
        """List all users."""
        return []

    @api_view.post
    def create_user(request, data: UserSchema) -> UserSchema:
        """Create a new user."""
        raise ApiError(400, "Not implemented")

    urlpatterns = [path("users/", methods(get=get_users, post=create_user))]

    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    path_item = spec.paths["/users/"]

    # Both methods should be present
    assert path_item.get is not None
    assert path_item.post is not None

    # Check each operation
    assert path_item.get.summary == "List all users."
    assert path_item.post.summary == "Create a new user."


def test_schema_serialization():
    """Test that OpenAPI spec serializes correctly to dict."""

    @api_view.get
    def simple_view(request) -> dict:
        """Simple view."""
        return {}

    urlpatterns = [path("simple/", simple_view)]

    config = OpenAPIConfig(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    # Serialize to dict
    spec_dict = spec.to_schema()

    # Verify dict structure
    assert isinstance(spec_dict, dict)
    assert spec_dict["openapi"] == "3.0.3"
    assert spec_dict["info"]["title"] == "Test API"
    assert "paths" in spec_dict
    assert "/simple/" in spec_dict["paths"]
