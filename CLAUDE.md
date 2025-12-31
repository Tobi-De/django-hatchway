# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

django-hatchway is a Django API framework that provides FastAPI-like type-annotated views while maintaining compatibility with standard Django patterns. It uses Pydantic for input validation and output serialization, with automatic parameter sourcing from URLs, query strings, request bodies, and files.

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
- Uses Pydantic models for input validation and output coercion
- `compile()` method analyzes view signatures at initialization time to build parameter routing
- `__call__()` method handles request processing, parameter extraction, validation, and response formatting

**hatchway/types.py** - Defines type annotations for explicit parameter sourcing:
- `Path[T]`, `Query[T]`, `Body[T]`, `File[T]` - single-source annotations
- `PathOrQuery[T]`, `QueryOrBody[T]` - multi-source fallback annotations
- `BodyDirect[T]` - forces Pydantic models to pull from top-level body keys
- `extract_signifier()` function unwraps these annotations to determine the source
- `acceptable_input()` validates that parameter types are supported

**hatchway/schema.py** - Django ORM integration:
- `Schema` extends Pydantic's `BaseModel` with `DjangoGetterDict`
- Automatically converts Django model instances to schema instances
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

### Parameter Sourcing Logic

The framework automatically determines parameter sources based on type hints:

1. **Simple types** (`int`, `str`, `float`): Path first, then Query
2. **Collections** (`list[int]`, `set[str]`): Query only, with implicit list conversion
3. **Pydantic models**: Body only (unless annotated with `BodyDirect`)
4. **Django File objects**: File only

**Body sourcing with multiple parameters**: When multiple parameters source from the body, each looks for a sub-key with its name. When only ONE parameter sources from the body and it's a BaseModel, it automatically switches to `body_direct` mode (top-level keys).

**Square bracket notation**: The framework supports `name[]` for lists and `name[key]` for dicts in query params and form data (see `get_values()` in view.py:130-164).

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
from hatchway import Schema, Field

class MySchema(Schema):
    name: str
    age: int = Field(gt=0)  # Pydantic validation

    # Can be instantiated from Django model instances due to DjangoGetterDict
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

## Important Notes

- The project requires Python 3.10+ and Django 4.0+
- Uses Pydantic v1.10 (note the `~=1.10` constraint in dependencies)
- All API views are automatically CSRF exempt (`csrf_exempt = True` on ApiView and Methods)
- PUT/PATCH requests require special handling for multipart and form data (see view.py:233-242)
- Input validation errors return 400 with `{"error": "invalid_input", "error_details": [...]}`
- Output types are optional but recommended for type safety throughout the view
