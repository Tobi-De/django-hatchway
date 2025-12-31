"""
Comprehensive demo of all Hatchway features:
- Path, Query, Body, File parameter sourcing
- QueryOrBody, PathOrQuery, BodyDirect
- Schema validation and ORM integration
- ApiResponse with custom headers/status
- ApiError handling
- Multiple HTTP methods on same URL
- File uploads
- List/dict return types
"""

import os

from django.core.files import File
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control

from hatchway import (
    ApiError,
    ApiResponse,
    Body,
    BodyDirect,
    PathOrQuery,
    Query,
    QueryOrBody,
    api_view,
)

from .models import Comment, Post
from .schemas import (
    CommentCreateSchema,
    CommentSchema,
    PostCreateSchema,
    PostListSchema,
    PostSchema,
    PostUpdateSchema,
)

# ============================================================================
# Basic GET requests with Path and Query parameters
# ============================================================================


@api_view.get
def post_list(
    request,
    published: QueryOrBody[bool | None] = None,
    limit: Query[int] = 10,
    offset: Query[int] = 0,
    tags: Query[list[str]] = [],
) -> list[PostListSchema]:
    """
    List posts with filtering and pagination.
    Demonstrates: Query parameters, QueryOrBody, list types, Schema output
    """
    queryset = Post.objects.all()

    # Filter by published status if provided
    if published is not None:
        queryset = queryset.filter(published=published)

    # Filter by tags if provided
    if tags:
        queryset = queryset.filter(tags__overlap=tags)

    # Apply pagination
    queryset = queryset[offset : offset + limit]

    # Return as list of schemas - Hatchway will convert ORM objects
    return list(queryset)


@api_view.get
def post_detail(request, id: int) -> PostSchema:
    """
    Get single post by ID.
    Demonstrates: Path parameter (from URL), Schema with ORM integration
    """
    post = get_object_or_404(Post, id=id)
    return post  # Will be converted to PostSchema automatically


# ============================================================================
# POST requests with Body parameters and validation
# ============================================================================


@api_view.post
def post_create(request, data: PostCreateSchema) -> ApiResponse[PostSchema]:
    """
    Create a new post.
    Demonstrates: Body parameter (BodyDirect - single model), ApiResponse with status
    """
    post = Post.objects.create(**data.dict())

    return ApiResponse(
        post,
        status=201,
        headers={"X-Created-Id": str(post.id)},
    )


@api_view.post
def post_create_with_file(
    request,
    title: str,
    content: str,
    author_id: Body[int],
    attachment: File | None = None,
) -> ApiResponse[dict]:
    """
    Create post with optional file upload.
    Demonstrates: Mixed parameter sources (query/body + file), File parameter
    Note: File handling simplified for demo without Pillow dependency
    """
    post = Post.objects.create(
        title=title, content=content, author_id=author_id, published=False
    )

    result = {"post_id": post.id, "title": post.title}
    if attachment:
        result["attachment_name"] = attachment.name
        result["attachment_size"] = attachment.size

    return ApiResponse(result, status=201)


# ============================================================================
# PATCH/PUT requests for updates
# ============================================================================


@api_view.patch
def post_update(request, id: int, data: PostUpdateSchema) -> PostSchema:
    """
    Update a post.
    Demonstrates: PATCH method, Path + Body combination
    """
    post = get_object_or_404(Post, id=id)

    # Update only provided fields
    for field, value in data.dict(exclude_unset=True).items():
        setattr(post, field, value)

    post.save()
    return post


# ============================================================================
# DELETE requests
# ============================================================================


@api_view.delete
def post_delete(request, id: int) -> dict:
    """
    Delete a post.
    Demonstrates: DELETE method, simple dict return
    """
    post = get_object_or_404(Post, id=id)
    post_id = post.id
    post.delete()

    return {"deleted": True, "id": post_id}


# ============================================================================
# Complex parameter sourcing examples
# ============================================================================


@api_view.get
def post_search(
    request,
    q: PathOrQuery[str],
    author_id: QueryOrBody[int | None] = None,
    include_unpublished: Query[bool] = False,
) -> list[PostListSchema]:
    """
    Search posts by query string.
    Demonstrates: PathOrQuery, QueryOrBody with optional types
    """
    queryset = Post.objects.filter(title__icontains=q)

    if author_id is not None:
        queryset = queryset.filter(author_id=author_id)

    if not include_unpublished:
        queryset = queryset.filter(published=True)

    return list(queryset[:20])


@api_view.post
def post_bulk_create(
    request,
    posts: Body[list[PostCreateSchema]],
    dry_run: QueryOrBody[bool] = False,
) -> ApiResponse[dict]:
    """
    Create multiple posts at once.
    Demonstrates: Body with list type, QueryOrBody for flags
    """
    if dry_run:
        return ApiResponse(
            {"would_create": len(posts), "posts": [p.dict() for p in posts]},
            status=200,
        )

    created_posts = []
    for post_data in posts:
        post = Post.objects.create(**post_data.dict())
        created_posts.append(post)

    return ApiResponse(
        {
            "created": len(created_posts),
            "ids": [p.id for p in created_posts],
        },
        status=201,
    )


# ============================================================================
# Nested resources and relationships
# ============================================================================


@api_view.get
def post_comments(request, post_id: int, limit: int = 10) -> list[CommentSchema]:
    """
    Get comments for a post.
    Demonstrates: Nested resource routing
    """
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()[:limit]
    return list(comments)


@api_view.post
def post_comment_create(
    request, post_id: int, comment: CommentCreateSchema
) -> ApiResponse[CommentSchema]:
    """
    Create a comment on a post.
    Demonstrates: Nested resource creation
    """
    post = get_object_or_404(Post, id=post_id)

    comment_obj = Comment.objects.create(post=post, **comment.dict())

    return ApiResponse(comment_obj, status=201)


# ============================================================================
# Error handling examples
# ============================================================================


@api_view.get
def post_stats(request, id: int, include_private: Query[bool] = False) -> dict:
    """
    Get post statistics.
    Demonstrates: ApiError for custom error responses
    """
    post = get_object_or_404(Post, id=id)

    if not post.published and not include_private:
        raise ApiError(status=403, error="Cannot view stats for unpublished posts")

    return {
        "id": post.id,
        "title": post.title,
        "comment_count": post.comments.count(),
        "tag_count": len(post.tags),
    }


# ============================================================================
# Square bracket notation examples
# ============================================================================


@api_view.post
def post_filter_advanced(
    request,
    filters: Body[dict[str, str | int]],
    options: Body[dict[str, bool]] = {},
) -> list[PostListSchema]:
    """
    Advanced filtering with dict parameters.
    Demonstrates: Dict body parameters (can use filters[key]=value notation)

    Example POST body (form-data):
      filters[title]=Django
      filters[author_id]=1
      options[published_only]=true
    """
    queryset = Post.objects.all()

    # Apply filters
    if "title" in filters:
        queryset = queryset.filter(title__icontains=filters["title"])
    if "author_id" in filters:
        queryset = queryset.filter(author_id=filters["author_id"])

    # Apply options
    if options.get("published_only"):
        queryset = queryset.filter(published=True)

    return list(queryset[:20])


# ============================================================================
# Response type variations
# ============================================================================


@api_view.get
def post_titles(request, author_id: int | None = None) -> list[str]:
    """
    Get just post titles.
    Demonstrates: Simple list[str] return type
    """
    queryset = Post.objects.all()
    if author_id is not None:
        queryset = queryset.filter(author_id=author_id)

    return list(queryset.values_list("title", flat=True))


@api_view.get
def post_tags_summary(request) -> dict[str, int]:
    """
    Get count of posts per tag.
    Demonstrates: dict return type
    """
    all_tags = Post.objects.values_list("tags", flat=True)
    tag_counts: dict[str, int] = {}

    for tags_list in all_tags:
        for tag in tags_list:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return tag_counts


# ============================================================================
# Health check / utility endpoints
# ============================================================================


@api_view.get
def health_check(request) -> dict:
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "posts_count": Post.objects.count(),
        "comments_count": Comment.objects.count(),
    }


# ============================================================================
# OpenAPI Documentation
# ============================================================================


def openapi_schema(request):
    """
    Serve the OpenAPI schema YAML file.
    Not using @api_view decorator since we want to return raw YAML.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "openapi.yaml")

    with open(schema_path) as f:
        schema_content = f.read()

    return HttpResponse(
        schema_content,
        content_type="application/x-yaml",
        headers={
            "Access-Control-Allow-Origin": "*",  # Allow CORS for external tools
        },
    )


@cache_control(max_age=3600)
def swagger_ui(request):
    """
    Serve Swagger UI for interactive API documentation.
    Uses the hosted Swagger UI with our OpenAPI schema.
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hatchway Demo API - Swagger UI</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <style>
            body { margin: 0; }
            .swagger-ui .topbar { display: none; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                window.ui = SwaggerUIBundle({
                    url: '/api/openapi.yaml',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout",
                    defaultModelsExpandDepth: 1,
                    defaultModelExpandDepth: 1,
                    docExpansion: "list",
                    filter: true,
                    tryItOutEnabled: true
                });
            };
        </script>
    </body>
    </html>
    """
    return HttpResponse(html, content_type="text/html")
