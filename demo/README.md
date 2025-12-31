# Hatchway Demo Project

This is a comprehensive demo application showcasing all features of the django-hatchway framework.

## Interactive API Documentation

**OpenAPI/Swagger UI**: `http://localhost:8000/api/docs/`

Try out all API endpoints interactively with full request/response examples and validation.

## Features Demonstrated

This demo includes a blog-style API with Posts and Comments that demonstrates:

### Parameter Sourcing
- **Path parameters**: `id: int` in URL patterns
- **Query parameters**: `limit: Query[int]`, `tags: Query[list[str]]`
- **Body parameters**: `data: PostCreateSchema`
- **File uploads**: `thumbnail: File`
- **PathOrQuery**: Checks path first, then query
- **QueryOrBody**: Checks query first, then body
- **BodyDirect**: Forces top-level body key extraction

### HTTP Methods
- `@api_view.get` - List and detail endpoints
- `@api_view.post` - Creation and bulk operations
- `@api_view.patch` - Partial updates
- `@api_view.delete` - Deletion
- `methods()` helper - Multiple methods on same URL

### Schema Features
- **ORM Integration**: Automatic conversion of Django models to schemas
- **Validation**: Pydantic field validators (min_length, max_length, ge, le)
- **Callable attributes**: `comment_count()` method auto-invoked by DjangoGetterDict
- **Optional fields**: Using `| None` for nullable fields
- **Nested schemas**: Comments nested under posts

### Response Types
- `dict` - Simple dictionary responses
- `list[Schema]` - List of schema objects
- `Schema` - Single schema object
- `ApiResponse[T]` - Custom headers and status codes
- `ApiError` - Structured error responses

### Advanced Features
- Square bracket notation for lists and dicts
- Bulk operations with validation
- Nested resource routing
- Custom error handling
- File uploads with multipart data

## API Endpoints

All endpoints are prefixed with `/api/`

### Documentation

- `GET /api/docs/` - Interactive Swagger UI documentation
- `GET /api/openapi.yaml` - OpenAPI 3.0 schema in YAML format

### Health

- `GET /api/health/` - Health check endpoint

### Posts

- `GET /api/posts/` - List posts (with filtering by published, tags, pagination)
- `GET /api/posts/<id>/` - Get post detail
- `PATCH /api/posts/<id>/` - Update post
- `DELETE /api/posts/<id>/` - Delete post
- `POST /api/posts/create/` - Create post
- `POST /api/posts/create-with-thumbnail/` - Create post with file upload
- `POST /api/posts/bulk/` - Bulk create posts
- `GET /api/posts/search/?q=<query>` - Search posts
- `GET /api/posts/<id>/stats/` - Get post statistics
- `POST /api/posts/filter/` - Advanced filtering with dict parameters
- `GET /api/posts/titles/` - Get just post titles
- `GET /api/posts/tags/summary/` - Get tag counts

### Comments

- `GET /api/posts/<post_id>/comments/` - List comments for a post
- `POST /api/posts/<post_id>/comments/create/` - Create comment on a post

## Quick Start

### From the demo directory:

```bash
# Run migrations
uv run python manage.py migrate

# Create a superuser
uv run python manage.py createsuperuser

# Run the development server
uv run python manage.py runserver
```

### Or using just (from project root):

```bash
# Setup everything
just demo-setup

# Run the server
just demo-serve

# Load demo data
just demo-data
```

## Testing the API

### Using the Interactive Documentation (Recommended)

Visit `http://localhost:8000/api/docs/` in your browser to use Swagger UI:
- View all endpoints organized by tags
- See request/response schemas with examples
- Try out endpoints directly in the browser
- View validation rules and constraints
- Download the OpenAPI schema

### Using curl:

```bash
# Health check
curl http://localhost:8000/api/health/

# List posts
curl http://localhost:8000/api/posts/

# Create a post
curl -X POST http://localhost:8000/api/posts/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "Hello Hatchway!",
    "author_id": 1,
    "published": true,
    "tags": ["tutorial", "django"]
  }'

# Search posts
curl "http://localhost:8000/api/posts/search/?q=First&include_unpublished=true"

# Create a comment
curl -X POST http://localhost:8000/api/posts/1/comments/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "author_name": "John Doe",
    "content": "Great post!",
    "rating": 5
  }'
```

### Using httpie:

```bash
# List posts with filters
http GET localhost:8000/api/posts/ published==true limit==5

# Create a post
http POST localhost:8000/api/posts/create/ \
  title="My Post" \
  content="Content here" \
  author_id:=1 \
  published:=true \
  tags:='["tag1", "tag2"]'

# Update a post
http PATCH localhost:8000/api/posts/1/ \
  published:=false

# Delete a post
http DELETE localhost:8000/api/posts/1/
```

## Admin Interface

Access the Django admin at `http://localhost:8000/admin/` to manage posts and comments through the web interface.

## Code Structure

- `models.py` - Django ORM models (Post, Comment)
- `schemas.py` - Pydantic schemas for validation and serialization
- `views.py` - API views with extensive comments explaining each feature
- `urls.py` - URL routing with examples of both direct mapping and `methods()` helper
- `admin.py` - Django admin configuration

## Performance Benchmarking

The project includes comprehensive performance benchmarks to track API and framework performance:

```bash
# Run all benchmarks
just bench

# Run only API benchmarks (from project root)
just bench-api

# Save performance baseline
just bench-save my-baseline

# Compare against baseline after making changes
just bench-compare-to my-baseline
```

See `../benchmarks/README.md` for detailed information on benchmarking.

## Learning Tips

1. Start by reading `views.py` - each view has detailed comments explaining what feature it demonstrates
2. Try each endpoint with different parameters to see how validation works
3. Look at `schemas.py` to see how Pydantic validators are applied
4. Check `urls.py` to see the `methods()` helper in action for multi-method routing
5. Experiment with the square bracket notation for lists and dicts in form data
6. Run benchmarks to understand performance characteristics
