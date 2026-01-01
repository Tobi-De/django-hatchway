"""OpenAPI integration for Hatchway."""

from openapi_spec_models import (
    JsonRenderPlugin,
    OpenAPIRenderPlugin,
    RapidocRenderPlugin,
    RedocRenderPlugin,
    ScalarRenderPlugin,
    StoplightRenderPlugin,
    SwaggerRenderPlugin,
    YamlRenderPlugin,
)

from .config import OpenAPIConfig
from .generator import OpenAPIGenerator
from .views import create_openapi_views

__all__ = (
    "OpenAPIConfig",
    "OpenAPIGenerator",
    "create_openapi_views",
    # Re-export plugins from openapi-spec-models
    "OpenAPIRenderPlugin",
    "JsonRenderPlugin",
    "YamlRenderPlugin",
    "RapidocRenderPlugin",
    "RedocRenderPlugin",
    "ScalarRenderPlugin",
    "StoplightRenderPlugin",
    "SwaggerRenderPlugin",
)
