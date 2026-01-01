# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

django-hatchway is a Django API framework that provides FastAPI-like type-annotated views while maintaining compatibility with standard Django patterns. It uses msgspec for high-performance input validation and output serialization, with automatic parameter sourcing from URLs, query strings, request bodies, and files.

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_view.py

# Run a specific test function
pytest tests/test_view.py::test_basic_view
```

### Benchmarking
```bash
# Run all benchmarks
just bench

# Run API benchmarks only
just bench-api

# Run framework internals benchmarks
just bench-internals

# Save baseline for comparison
just bench-save baseline

# Compare against baseline
just bench-compare-to baseline

# Generate HTML report
just bench-html
```

See `benchmarks/README.md` for detailed benchmarking guide.

### Code Quality
```bash
# Run pre-commit hooks manually
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
```

The project uses:
- **black** for code formatting
- **isort** for import sorting (with `--profile=black`)
- **flake8** for linting (max line length: 119)
- **mypy** for type checking (excludes tests/)
- **pyupgrade** with `--py310-plus` for Python 3.10+ syntax

### Building
```bash
# Build package (uses uv_build)
python3 -m build
```

### Package Management
This project uses **uv** for dependency management. The `pyproject.toml` uses `uv_build` as the build backend.

## Architecture

### Core Components

**hatchway/view.py** - The `ApiView` class is the central request processor:
- Wraps function-based views with `@api_view.get`, `@api_view.post`, etc. decorators
- Introspects function type hints to determine where to source each parameter (path, query, body, file)
- Uses msgspec for input validation and output coercion
- `compile()` method analyzes view signatures at initialization time to build parameter routing
- `__call__()` method handles request processing, parameter extraction, validation, and response formatting

**hatchway/types.py** - Defines type annotations for explicit parameter sourcing:
- `Path[T]`, `Query[T]`, `Body[T]`, `File[T]` - single-source annotations
- `PathOrQuery[T]`, `QueryOrBody[T]` - multi-source fallback annotations
- `BodyDirect[T]` - forces Schema models to pull from top-level body keys
- `extract_signifier()` function unwraps these annotations to determine the source
- `acceptable_input()` validates that parameter types are supported

**hatchway/schema.py** - Django ORM integration:
- `Schema` extends `msgspec.Struct` for high-performance serialization
- Automatically converts Django model instances to schema instances via `from_orm()`
- Handles Django-specific types: `Manager`, `QuerySet`, `FieldFile` (converts to URL)
- Supports callable attributes (methods) by automatically calling them

**hatchway/http.py** - Response handling:
- `ApiResponse[T]` - Generic JSON response wrapper (extends Django's `HttpResponse`)
- `ApiError` - Exception class for returning structured errors with status codes
- Response finalization converts Python objects to JSON using `DjangoJSONEncoder`

**hatchway/urls.py** - The `Methods` class enables multi-method routing:
```python
path("api/item/<id>/", methods(get=item_get, delete=item_delete))
```

**hatchway/models.py** - Authentication token model:
- `AuthToken` - Database model for token-based authentication
- Stores secure tokens with expiration dates
- Class method `create_token(user, days_valid=365, description="")` generates secure tokens
- Property `is_expired` checks token validity

**hatchway/auth.py** - Authentication backend system:
- `AuthBackend` - Protocol defining the authentication backend interface
- `SessionAuthBackend` - Authenticates via Django's session middleware (`request.user`)
- `TokenAuthBackend` - Authenticates via `Authorization: Token <token>` header
- `authenticate_request(request, backends=None)` - Tries backends in sequence, returns `(user, backend_name)` tuple
- `get_default_backends()` - Loads backends from `HATCHWAY_AUTH_BACKENDS` setting or uses defaults

**hatchway/permissions.py** - Permission checking utilities:
- `check_permissions(user, permissions)` - Validates user has all required Django permissions
- `require_authentication(user)` - Validates user is authenticated
- Both return `(bool, error_msg)` tuples for consistent error handling

### Parameter Sourcing Logic

The framework automatically determines parameter sources based on type hints:

1. **Simple types** (`int`, `str`, `float`): Path first, then Query
2. **Collections** (`list[int]`, `set[str]`): Query only, with implicit list conversion
3. **Schema models**: Body only (unless annotated with `BodyDirect`)
4. **Django File objects**: File only

**Body sourcing with multiple parameters**: When multiple parameters source from the body, each looks for a sub-key with its name. When only ONE parameter sources from the body and it's a Schema model, it automatically switches to `body_direct` mode (top-level keys).

**Square bracket notation**: The framework supports `name[]` for lists and `name[key]` for dicts in query params and form data (see `get_values()` in view.py:130-164).

### Authentication Flow

The `ApiView` class integrates authentication through decorator parameters:

```python
@api_view.get(auth=True, permissions=["app.permission"])
def protected_view(request) -> dict:
    # request.user is guaranteed to be authenticated with the permission
    return {"user_id": request.user.id}
```

**Authentication processing happens in `ApiView.__call__()`** after method checking but before input parsing:

1. **Backend selection**: If `auth` is a list of backend class paths, instantiate them; otherwise use defaults
2. **Authentication attempt**: Call `authenticate_request(request, backends)` which tries backends in sequence
3. **User assignment**: If successful, set `request.user` to the authenticated user
4. **Auth requirement check**: If `auth=True`, verify user is authenticated (return 401 if not)
5. **Permission check**: If `permissions` list provided, verify user has all perms (return 401 or 403 if not)
6. **Continue to input parsing**: Only reached if all auth/permission checks pass

**Error responses**:
- **401 Unauthorized**: `{"error": "authentication_required"}` - User not authenticated
- **403 Forbidden**: `{"error": "permission_denied"}` - User lacks required permission

**Backend sequencing**: Backends are tried in order until one returns a user. Default order: SessionAuthBackend, then TokenAuthBackend. This allows requests to use either session cookies or API tokens.

### Test Structure

Tests are in `tests/` directory with Django settings at `tests/test_project/settings.py`. The pytest configuration in `pyproject.toml` sets:
- `DJANGO_SETTINGS_MODULE="tests.test_project.settings"`
- `django_find_project = false`

Tests use Django's `RequestFactory` to simulate requests without requiring a running server.

## Code Patterns

### Creating API Views

```python
from hatchway import api_view, Schema, Body, QueryOrBody

@api_view.get
def my_endpoint(request, id: int, limit: int = 100) -> list[str]:
    # id comes from path or query, limit from query
    ...

@api_view.post
def create_item(request, data: MySchema, mode: Body[str] = "normal") -> int:
    # data comes from body (direct if only body param)
    # mode explicitly from body
    ...
```

### Schema Definition

```python
from typing import Annotated
from hatchway import Schema, Meta

class MySchema(Schema):
    name: str
    age: Annotated[int, Meta(gt=0)]  # msgspec validation

    # Can be instantiated from Django model instances via from_orm()
```

### Error Handling

```python
from hatchway import ApiError

# Raise structured errors
raise ApiError(status=404, error="Item not found")

# Returns: {"error": "Item not found"} with 404 status
```

### Response Customization

```python
from hatchway import ApiResponse

@api_view.get
def my_view(request) -> ApiResponse[dict]:
    return ApiResponse(
        {"data": "value"},
        headers={"X-Custom": "header"},
        status=201
    )
```

### Authentication & Permissions

```python
from hatchway import api_view, ApiError

# Basic authentication requirement
@api_view.get(auth=True)
def user_profile(request) -> dict:
    return {
        "user_id": request.user.id,
        "username": request.user.username
    }

# Authentication + permission check
@api_view.post(auth=True, permissions=["blog.add_post"])
def create_post(request, data: PostSchema) -> PostSchema:
    post = Post.objects.create(author=request.user, **data.dict())
    return post

# Custom backend selection (token-only, no sessions)
@api_view.get(auth=["hatchway.auth.TokenAuthBackend"])
def api_only(request) -> dict:
    return {"message": "Token auth only"}

# Manual permission/ownership check
@api_view.delete(auth=True)
def delete_post(request, id: int) -> dict:
    post = get_object_or_404(Post, id=id)
    if post.author != request.user:
        raise ApiError(403, "You can only delete your own posts")
    post.delete()
    return {"deleted": True}
```

### OpenAPI Specification Generation

Hatchway provides automatic OpenAPI 3.0 specification generation from your API views.

**Module**: `hatchway.openapi`

**Key Components**:
- `OpenAPIConfig` - Configuration for OpenAPI spec generation
- `OpenAPIGenerator` - Generates OpenAPI spec from URL patterns
- `create_openapi_views()` - Factory function to create documentation views
- `openapi_json_view`, `openapi_yaml_view`, `swagger_ui_view` - Pre-built view functions

**How it works**:
1. Introspects Django URL patterns to find `ApiView` and `Methods` instances
2. Extracts parameter information from type hints (Path, Query, Body, File types)
3. Generates OpenAPI schema from `msgspec.Struct` models with validation constraints
4. Creates complete OpenAPI 3.0 spec with paths, operations, parameters, request bodies, responses

**Setup Example** (see `demo/api/urls.py`):

```python
from django.urls import path
from hatchway import methods
from hatchway.openapi import OpenAPIConfig, create_openapi_views
from . import views

# Define your API endpoints
api_endpoints = [
    path("posts/", views.post_list, name="post_list"),
    path("posts/create/", views.post_create, name="post_create"),
    path("posts/<int:id>/", methods(
        get=views.post_detail,
        patch=views.post_update,
        delete=views.post_delete,
    )),
]

# Configure OpenAPI
openapi_config = OpenAPIConfig(
    title="My API",
    version="1.0.0",
    description="My awesome API",
    contact={"name": "Support", "email": "support@example.com"},
    license={"name": "MIT"},
    servers=[{"url": "http://localhost:8000/api"}],
    tags=[
        {"name": "posts", "description": "Blog post management"},
    ],
)

# Generate OpenAPI views
openapi_json, openapi_yaml, swagger_ui = create_openapi_views(
    openapi_config, api_endpoints
)

# Add to URL patterns
urlpatterns = [
    path("docs/", swagger_ui, name="swagger_ui"),
    path("openapi.json", openapi_json, name="openapi_json"),
    path("openapi.yaml", openapi_yaml, name="openapi_yaml"),
] + api_endpoints
```

**Schema Generation**:
- Automatically converts `msgspec.Struct` to OpenAPI schemas
- Preserves validation constraints (min/max, length, pattern, etc.) from msgspec.Meta
- Supports nested schemas, lists, dicts, unions, and optional types
- Generates proper `$ref` references for reusable schemas

**Parameter Detection**:
- Path parameters: Extracted from URL patterns (`<int:id>` → path parameter)
- Query parameters: From `Query[T]`, `PathOrQuery[T]`, `QueryOrBody[T]` annotations
- Body parameters: From `Body[T]`, `BodyDirect[T]`, or Schema models
- File parameters: From `File[T]` annotations
- Default values and required status automatically detected from function signatures

**Response Generation**:
- Success response schema from function return type hint
- Automatic status code selection (201 for POST, 200 for others)
- Standard error responses (400 validation, 401 auth, 403 permission)
- Supports `ApiResponse[T]` for custom headers/status

**Authentication & Security**:
- Detects `auth=True` and `permissions=[]` decorators
- Adds security requirements to operations
- Can be customized with security schemes in OpenAPIConfig

## Important Notes

- The project requires Python 3.10+ and Django 4.0+
- Uses msgspec>=0.18.0 for high-performance serialization
- All API views are automatically CSRF exempt (`csrf_exempt = True` on ApiView and Methods)
- PUT/PATCH requests require special handling for multipart and form data
- Input validation errors return 400 with `{"error": "invalid_input", "error_details": [...]}`
- Output types are optional but recommended for type safety throughout the view
- Schema models use `msgspec.Struct` with `omit_defaults=True` and `gc=False` for optimal performance
- Authentication happens after method check but before input parsing (early exit for unauthorized requests)
- `auth` parameter accepts `True` (use defaults), `False` (no auth), or list of backend class paths
- `permissions` parameter implies `auth=True` (authentication is required to check permissions)
- Use custom `HATCHWAY_AUTH_BACKENDS` setting (not Django's `AUTHENTICATION_BACKENDS`) for API auth configuration
- AuthToken model requires running migrations: `python manage.py migrate`
