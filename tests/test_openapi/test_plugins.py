"""Tests for OpenAPI render plugins."""

import json

import pytest
from django.http import HttpRequest
from django.test import RequestFactory

from openapi_spec_models import (
    JsonRenderPlugin,
    RapidocRenderPlugin,
    RedocRenderPlugin,
    ScalarRenderPlugin,
    StoplightRenderPlugin,
    SwaggerRenderPlugin,
    YamlRenderPlugin,
)


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI specification for testing."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test/": {
                "get": {
                    "summary": "Test endpoint",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }


@pytest.fixture
def request_factory():
    """Django request factory."""
    return RequestFactory()


def test_json_plugin_render(sample_openapi_spec, request_factory):
    """Test JsonRenderPlugin renders JSON correctly."""
    plugin = JsonRenderPlugin(path="/openapi.json")
    request = request_factory.get("/openapi.json")

    result = plugin.render(sample_openapi_spec)

    # Should return JSON bytes
    assert isinstance(result, bytes)

    # Should be valid JSON
    parsed = json.loads(result)
    assert parsed["openapi"] == "3.0.3"
    assert parsed["info"]["title"] == "Test API"


def test_json_plugin_media_type():
    """Test JsonRenderPlugin has correct media type."""
    plugin = JsonRenderPlugin()
    assert plugin.media_type == "application/json"


def test_yaml_plugin_render(sample_openapi_spec, request_factory):
    """Test YamlRenderPlugin renders YAML correctly."""
    pytest.importorskip("yaml")  # Skip if PyYAML not installed

    plugin = YamlRenderPlugin(path="/openapi.yaml")
    request = request_factory.get("/openapi.yaml")

    result = plugin.render(sample_openapi_spec)

    # Should return bytes
    assert isinstance(result, bytes)

    # Should contain YAML content
    content = result.decode("utf-8")
    assert "openapi:" in content
    assert "3.0.3" in content
    assert "Test API" in content


def test_yaml_plugin_missing_dependency(sample_openapi_spec, request_factory, monkeypatch):
    """Test YamlRenderPlugin raises error if PyYAML is not installed."""
    # Mock yaml import to fail
    import sys

    monkeypatch.setitem(sys.modules, "yaml", None)

    plugin = YamlRenderPlugin()
    request = request_factory.get("/openapi.yaml")

    with pytest.raises(RuntimeError, match="PyYAML is required"):
        plugin.render(sample_openapi_spec)


def test_swagger_plugin_render(sample_openapi_spec, request_factory):
    """Test SwaggerRenderPlugin renders HTML correctly."""
    plugin = SwaggerRenderPlugin(path="/swagger")
    request = request_factory.get("/swagger")

    result = plugin.render(sample_openapi_spec)

    # Should return HTML bytes
    assert isinstance(result, bytes)
    html = result.decode("utf-8")

    # Should contain Swagger UI elements
    assert "<!DOCTYPE html>" in html
    assert "swagger-ui" in html
    assert "SwaggerUIBundle" in html
    assert "Test API" in html


def test_swagger_plugin_custom_version():
    """Test SwaggerRenderPlugin with custom version."""
    plugin = SwaggerRenderPlugin(version="5.0.0")
    assert "5.0.0" in plugin.js_url
    assert "5.0.0" in plugin.css_url


def test_swagger_plugin_custom_urls():
    """Test SwaggerRenderPlugin with custom JS/CSS URLs."""
    plugin = SwaggerRenderPlugin(
        js_url="https://example.com/swagger.js", css_url="https://example.com/swagger.css"
    )
    assert plugin.js_url == "https://example.com/swagger.js"
    assert plugin.css_url == "https://example.com/swagger.css"


def test_redoc_plugin_render(sample_openapi_spec, request_factory):
    """Test RedocRenderPlugin renders HTML correctly."""
    plugin = RedocRenderPlugin(path="/redoc")
    request = request_factory.get("/redoc")

    result = plugin.render(sample_openapi_spec)

    html = result.decode("utf-8")
    assert "<!DOCTYPE html>" in html
    assert "redoc" in html.lower()
    assert "Redoc.init" in html
    assert "Test API" in html


def test_scalar_plugin_render(sample_openapi_spec, request_factory):
    """Test ScalarRenderPlugin renders HTML correctly."""
    plugin = ScalarRenderPlugin(path="/scalar")
    request = request_factory.get("/scalar")

    result = plugin.render(sample_openapi_spec)

    html = result.decode("utf-8")
    assert "<!DOCTYPE html>" in html
    assert "scalar" in html.lower()
    assert "api-reference" in html
    assert "Test API" in html


def test_rapidoc_plugin_render(sample_openapi_spec, request_factory):
    """Test RapidocRenderPlugin renders HTML correctly."""
    plugin = RapidocRenderPlugin(path="/rapidoc")
    request = request_factory.get("/rapidoc")

    result = plugin.render(sample_openapi_spec)

    html = result.decode("utf-8")
    assert "<!DOCTYPE html>" in html
    assert "rapi-doc" in html
    assert "Test API" in html


def test_stoplight_plugin_render(sample_openapi_spec, request_factory):
    """Test StoplightRenderPlugin renders HTML correctly."""
    plugin = StoplightRenderPlugin(path="/elements")
    request = request_factory.get("/elements")

    result = plugin.render(sample_openapi_spec)

    html = result.decode("utf-8")
    assert "<!DOCTYPE html>" in html
    assert "elements-api" in html
    assert "Test API" in html


def test_plugin_paths():
    """Test that plugins correctly handle path configuration."""
    # Single path
    plugin = JsonRenderPlugin(path="/openapi.json")
    assert plugin.paths == ["/openapi.json"]
    assert plugin.has_path("/openapi.json")
    assert not plugin.has_path("/other.json")

    # Multiple paths
    plugin = JsonRenderPlugin(path=["/openapi.json", "/schema.json"])
    assert len(plugin.paths) == 2
    assert plugin.has_path("/openapi.json")
    assert plugin.has_path("/schema.json")


def test_plugin_custom_favicon():
    """Test plugins with custom favicon."""
    custom_favicon = '<link rel="icon" href="/custom-icon.png">'
    plugin = SwaggerRenderPlugin(favicon=custom_favicon)
    request = RequestFactory().get("/swagger")
    result = plugin.render({"info": {"title": "Test"}})
    html = result.decode("utf-8")
    assert "/custom-icon.png" in html


def test_plugin_custom_style():
    """Test plugins with custom CSS style."""
    custom_style = "<style>body { background: red; }</style>"
    plugin = SwaggerRenderPlugin(style=custom_style)
    request = RequestFactory().get("/swagger")
    result = plugin.render({"info": {"title": "Test"}})
    html = result.decode("utf-8")
    assert "background: red" in html
