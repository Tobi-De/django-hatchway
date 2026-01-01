from django.urls import path

from hatchway import methods
from hatchway.openapi import OpenAPIConfig, create_openapi_views

from . import views

# Define API endpoints first
api_endpoints = [
    # Health check
    path("health/", views.health_check, name="health_check"),
    # Authentication
    path("auth/token/", views.obtain_token, name="obtain_token"),
    # Post list and creation
    path("posts/", views.post_list, name="post_list"),
    path("posts/create/", views.post_create, name="post_create"),
    path(
        "posts/create-with-file/",
        views.post_create_with_file,
        name="post_create_with_file",
    ),
    path("posts/bulk/", views.post_bulk_create, name="post_bulk_create"),
    # Post detail, update, delete - demonstrates methods() helper
    path(
        "posts/<int:id>/",
        methods(
            get=views.post_detail,
            patch=views.post_update,
            delete=views.post_delete,
        ),
        name="post_detail",
    ),
    # Post search and stats
    path("posts/search/", views.post_search, name="post_search"),
    path("posts/<int:id>/stats/", views.post_stats, name="post_stats"),
    # Post filtering
    path("posts/filter/", views.post_filter_advanced, name="post_filter_advanced"),
    # Post utilities
    path("posts/titles/", views.post_titles, name="post_titles"),
    path("posts/tags/summary/", views.post_tags_summary, name="post_tags_summary"),
    # Comments (nested under posts)
    path("posts/<int:post_id>/comments/", views.post_comments, name="post_comments"),
    path(
        "posts/<int:post_id>/comments/create/",
        views.post_comment_create,
        name="post_comment_create",
    ),
    # Authenticated endpoints (examples)
    path("user/profile/", views.user_profile, name="user_profile"),
    path(
        "posts/create-protected/",
        views.post_create_protected,
        name="post_create_protected",
    ),
    path(
        "posts/<int:id>/delete-auth/",
        views.post_delete_auth,
        name="post_delete_auth",
    ),
    path("api-only/", views.api_only_endpoint, name="api_only_endpoint"),
]

# Configure OpenAPI
openapi_config = OpenAPIConfig(
    title="Hatchway Demo API",
    version="1.0.0",
    description="""
Comprehensive demonstration of django-hatchway framework features.

This API showcases:
- Type-safe parameter sourcing (Path, Query, Body, File)
- msgspec schema validation
- Multiple HTTP methods
- Nested resources
- File uploads
- Custom error handling

Built with [django-hatchway](https://github.com/andrewgodwin/django-hatchway)
""".strip(),
    contact={"name": "Hatchway Demo"},
    license={"name": "BSD-3-Clause"},
    servers=[{"url": "http://localhost:8000/api", "description": "Development server"}],
    tags=[
        {"name": "health", "description": "Health check endpoints"},
        {"name": "auth", "description": "Authentication endpoints"},
        {"name": "posts", "description": "Blog post management"},
        {"name": "comments", "description": "Comment management"},
    ],
)

# Generate OpenAPI views (returns dict of {path: view_func})
openapi_views = create_openapi_views(openapi_config, api_endpoints)

# Complete URL patterns with OpenAPI documentation
urlpatterns = [
    # OpenAPI Documentation
    path("docs/", openapi_views["/swagger"], name="swagger_ui"),
    path("openapi.json", openapi_views["/openapi.json"], name="openapi_json"),
    path("openapi.yaml", openapi_views["/openapi.yaml"], name="openapi_yaml"),
] + api_endpoints
