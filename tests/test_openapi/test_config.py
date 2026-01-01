"""Tests for OpenAPIConfig configuration."""

import pytest

from hatchway.openapi import (
    OpenAPIConfig,
    OpenAPIGenerator,
    RedocRenderPlugin,
    SwaggerRenderPlugin,
)
from openapi_spec_models import Components, Example, Schema


def test_config_basic():
    """Test basic OpenAPIConfig initialization."""
    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        description="Test description",
    )

    assert config.title == "Test API"
    assert config.version == "1.0.0"
    assert config.description == "Test description"


def test_config_with_servers():
    """Test OpenAPIConfig with server configuration."""
    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        servers=[
            {"url": "https://api.example.com", "description": "Production"},
            {"url": "http://localhost:8000", "description": "Development"},
        ],
    )

    assert len(config.servers) == 2
    assert config.servers[0]["url"] == "https://api.example.com"


def test_config_with_tags():
    """Test OpenAPIConfig with tags."""
    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        tags=[
            {"name": "users", "description": "User management"},
            {"name": "posts", "description": "Post management"},
        ],
    )

    assert len(config.tags) == 2
    assert config.tags[0]["name"] == "users"
    assert config.tags[1]["name"] == "posts"


def test_config_with_contact():
    """Test OpenAPIConfig with contact information."""
    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        contact={"name": "API Support", "email": "support@example.com"},
    )

    assert config.contact["name"] == "API Support"
    assert config.contact["email"] == "support@example.com"


def test_config_with_license():
    """Test OpenAPIConfig with license information."""
    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        license={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    )

    assert config.license["name"] == "MIT"
    assert config.license["url"] == "https://opensource.org/licenses/MIT"


def test_config_with_external_docs():
    """Test OpenAPIConfig with external documentation."""
    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        external_docs={"url": "https://docs.example.com", "description": "Full documentation"},
    )

    assert config.external_docs["url"] == "https://docs.example.com"


def test_config_with_security():
    """Test OpenAPIConfig with global security requirements."""
    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        security=[{"TokenAuth": []}],
    )

    assert len(config.security) == 1
    assert config.security[0] == {"TokenAuth": []}


def test_config_with_components():
    """Test OpenAPIConfig with custom components."""
    custom_components = {
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"},
                },
            }
        }
    }

    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        components=custom_components,
    )

    assert config.components is not None
    assert "Error" in config.components["schemas"]


def test_default_components_include_security_schemes():
    """Test that default components include security schemes."""
    config = OpenAPIConfig(title="Test API", version="1.0.0")

    components = config._get_default_components()

    assert "security_schemes" in components
    assert "TokenAuth" in components["security_schemes"]
    assert "SessionAuth" in components["security_schemes"]

    # Check TokenAuth configuration
    token_auth = components["security_schemes"]["TokenAuth"]
    assert token_auth["type"] == "apiKey"
    assert token_auth["in"] == "header"
    assert token_auth["name"] == "Authorization"

    # Check SessionAuth configuration
    session_auth = components["security_schemes"]["SessionAuth"]
    assert session_auth["type"] == "apiKey"
    assert session_auth["in"] == "cookie"
    assert session_auth["name"] == "sessionid"


def test_config_merges_custom_components_with_defaults():
    """Test that custom components merge with default security schemes."""
    custom_components = {
        "schemas": {
            "CustomSchema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            }
        }
    }

    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        components=custom_components,
    )

    # Generate spec to see merged components
    from django.urls import path
    from hatchway import api_view

    @api_view.get
    def test_view(request) -> dict:
        return {}

    urlpatterns = [path("test/", test_view)]
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    # Should have both custom schemas and security schemes
    assert spec.components is not None
    assert spec.components.security_schemes is not None
    assert "TokenAuth" in spec.components.security_schemes
    assert "SessionAuth" in spec.components.security_schemes


def test_to_openapi_schema_dict():
    """Test converting config to OpenAPI schema dict."""
    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        description="Test description",
        tags=[{"name": "test", "description": "Test tag"}],
    )

    schema = config.to_openapi_base()

    assert schema["openapi"] == "3.0.3"
    assert schema["info"]["title"] == "Test API"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["description"] == "Test description"
    assert schema["tags"][0]["name"] == "test"


def test_terms_of_service():
    """Test OpenAPIConfig with terms of service."""
    config = OpenAPIConfig(
        title="Test API",
        version="1.0.0",
        terms_of_service="https://example.com/terms",
    )

    assert config.terms_of_service == "https://example.com/terms"

    schema = config.to_openapi_base()
    assert schema["info"]["termsOfService"] == "https://example.com/terms"
