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

from django.core.files import File
from django.shortcuts import get_object_or_404

from hatchway import (
    ApiError,
    ApiResponse,
    Body,
    BodyDirect,
    PathOrQuery,
    Query,
    QueryOrBody,
    Schema,
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

    # Update only provided fields (non-None values)
    # Note: msgspec doesn't track unset fields, so we filter None values
    for field, value in data.dict().items():
        if value is not None:
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
    request, post_id: int, comment: CommentCreateSchema, validate_output=False
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
# Authentication Examples
# ============================================================================


class LoginRequest(Schema):
    """Schema for login credentials."""

    username: str
    password: str


class TokenResponse(Schema):
    """Schema for token response."""

    token: str
    expires_at: str


@api_view.post
def obtain_token(request, credentials: LoginRequest) -> TokenResponse:
    """
    Obtain an authentication token.
    Demonstrates: Token creation endpoint, authentication
    """
    from django.contrib.auth import authenticate

    from hatchway.models import AuthToken

    # Authenticate the user
    user = authenticate(username=credentials.username, password=credentials.password)

    if user is None:
        raise ApiError(401, "Invalid credentials")

    # Create a token for the user
    token = AuthToken.create_token(
        user=user, days_valid=365, description="API access via login"
    )

    return TokenResponse(token=token.token, expires_at=token.expires.isoformat())


@api_view.get(auth=True)
def user_profile(request) -> dict:
    """
    Protected endpoint - requires authentication.
    Accepts both session and token authentication.
    """
    return {
        "user_id": request.user.id,
        "username": request.user.username,
        "email": request.user.email,
    }


@api_view.post(auth=True, permissions=["api.add_post"])
def post_create_protected(request, data: PostCreateSchema) -> PostSchema:
    """
    Protected endpoint - requires authentication and 'api.add_post' permission.
    Demonstrates permission checking.
    """
    post = Post.objects.create(author=request.user, **data.dict())
    return post


@api_view.delete(auth=True)
def post_delete_auth(request, id: int) -> dict:
    """
    Protected delete - requires authentication.
    Only allows users to delete their own posts.
    """
    post = get_object_or_404(Post, id=id)

    # Only allow users to delete their own posts
    if post.author != request.user:
        raise ApiError(403, "You can only delete your own posts")

    post.delete()
    return {"deleted": True}


@api_view.get(auth=["hatchway.auth.TokenAuthBackend"])
def api_only_endpoint(request) -> dict:
    """
    API-only endpoint - only accepts token authentication, not sessions.
    Demonstrates custom backend selection.
    """
    return {
        "message": "This endpoint only accepts token authentication",
        "user_id": request.user.id,
    }
