"""
Views for serving OpenAPI specifications and documentation UI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponse
from openapi_spec_models import OpenAPIRenderPlugin

if TYPE_CHECKING:
    from .config import OpenAPIConfig
    from .generator import OpenAPIGenerator


def create_plugin_view(plugin: OpenAPIRenderPlugin, spec_dict: dict) -> callable:
    """
    Create a Django view function for a render plugin.

    Args:
        plugin: The render plugin instance
        spec_dict: The OpenAPI specification as a dictionary

    Returns:
        View function that renders the plugin
    """

    def view(request: HttpRequest) -> HttpResponse:
        content = plugin.render(spec_dict)
        return HttpResponse(content, content_type=plugin.media_type)

    # Set view name for URL routing
    view.__name__ = f"{plugin.__class__.__name__}_view"
    return view


def create_openapi_views(
    config: OpenAPIConfig, urlpatterns, render_plugins: list[OpenAPIRenderPlugin] | None = None
) -> dict[str, callable]:
    """
    Create OpenAPI view functions with a specific configuration.

    This is a factory function that creates view functions for rendering OpenAPI
    documentation in various formats using render plugins.

    Args:
        config: OpenAPI configuration
        urlpatterns: Django URL patterns to document
        render_plugins: List of render plugins to use. If None, uses SwaggerUI + JSON + YAML

    Returns:
        Dictionary mapping plugin paths to view functions

    Example:
        from hatchway.openapi import (
            OpenAPIConfig,
            create_openapi_views,
            SwaggerRenderPlugin,
            RedocRenderPlugin,
        )

        config = OpenAPIConfig(title="My API", version="1.0.0")
        plugins = [
            SwaggerRenderPlugin(path="/swagger"),
            RedocRenderPlugin(path="/redoc"),
        ]

        views = create_openapi_views(config, urlpatterns, plugins)

        # In urls.py:
        urlpatterns = [
            path("swagger/", views["/swagger"]),
            path("redoc/", views["/redoc"]),
        ]
    """
    from openapi_spec_models import JsonRenderPlugin, SwaggerRenderPlugin, YamlRenderPlugin

    from .generator import OpenAPIGenerator

    # Use default plugins if none provided
    if render_plugins is None:
        render_plugins = [
            SwaggerRenderPlugin(path="/swagger"),
            JsonRenderPlugin(path="/openapi.json"),
            YamlRenderPlugin(path="/openapi.yaml"),
        ]

    # Create generator and generate spec
    generator = OpenAPIGenerator(config)
    spec = generator.generate(urlpatterns)

    # Convert spec to dictionary
    spec_dict = spec.to_schema()

    # Create views for each plugin
    views = {}
    for plugin in render_plugins:
        # Plugins can have multiple paths
        view_func = create_plugin_view(plugin, spec_dict)
        for path in plugin.paths:
            views[path] = view_func

    return views


# Legacy compatibility functions (deprecated - use create_openapi_views with plugins instead)

def openapi_json_view(request: HttpRequest) -> HttpResponse:
    """
    Deprecated: Use create_openapi_views with JsonRenderPlugin instead.

    Serves the OpenAPI specification as JSON.
    """
    # This is kept for backward compatibility but should be replaced
    # with the plugin-based approach
    raise NotImplementedError(
        "Use create_openapi_views with JsonRenderPlugin instead of calling this directly"
    )


def openapi_yaml_view(request: HttpRequest) -> HttpResponse:
    """
    Deprecated: Use create_openapi_views with YamlRenderPlugin instead.

    Serves the OpenAPI specification as YAML.
    """
    raise NotImplementedError(
        "Use create_openapi_views with YamlRenderPlugin instead of calling this directly"
    )


def swagger_ui_view(request: HttpRequest) -> HttpResponse:
    """
    Deprecated: Use create_openapi_views with SwaggerRenderPlugin instead.

    Serves Swagger UI for interactive API documentation.
    """
    raise NotImplementedError(
        "Use create_openapi_views with SwaggerRenderPlugin instead of calling this directly"
    )
