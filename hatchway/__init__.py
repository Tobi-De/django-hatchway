import msgspec

from .http import ApiError, ApiResponse  # noqa
from .schema import Schema  # noqa
from .types import Body, BodyDirect, File, Path, PathOrQuery, Query, QueryOrBody  # noqa
from .urls import methods  # noqa
from .view import api_view  # noqa

# Re-export msgspec.Meta for convenience
Meta = msgspec.Meta  # noqa

__all__ = [
    # Core
    "api_view",
    "methods",
    "Schema",
    "Meta",
    # HTTP
    "ApiResponse",
    "ApiError",
    # Types
    "Path",
    "Query",
    "Body",
    "File",
    "PathOrQuery",
    "QueryOrBody",
    "BodyDirect",
    # Auth (lazy-loaded)
    "SessionAuthBackend",
    "TokenAuthBackend",
    "authenticate_request",
    "AuthToken",
    "check_permissions",
    "require_authentication",
]

# Lazy imports for auth-related components (to avoid Django app registry issues)
_LAZY_IMPORTS = {
    "SessionAuthBackend": ".auth",
    "TokenAuthBackend": ".auth",
    "authenticate_request": ".auth",
    "AuthToken": ".models",
    "check_permissions": ".permissions",
    "require_authentication": ".permissions",
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        module = import_module(_LAZY_IMPORTS[name], __package__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
