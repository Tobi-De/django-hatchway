from datetime import datetime
from typing import Annotated

from hatchway import Meta, Schema


class PostSchema(Schema):
    """Schema for Post model - demonstrates ORM mode"""

    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    updated_at: datetime
    published: bool
    tags: list[str]
    comment_count: int  # Callable method will be auto-invoked


class PostListSchema(Schema):
    """Simplified schema for listing posts"""

    id: int
    title: str
    author_id: int
    created_at: datetime
    published: bool
    comment_count: int


class PostCreateSchema(Schema):
    """Schema for creating posts - demonstrates input validation"""

    title: Annotated[str, Meta(min_length=1, max_length=200)]
    content: Annotated[str, Meta(min_length=1)]
    author_id: Annotated[int, Meta(gt=0)]
    published: bool = False
    tags: list[str] = []


class PostUpdateSchema(Schema):
    """Schema for updating posts - all fields optional"""

    title: Annotated[str, Meta(min_length=1, max_length=200)] | None = None
    content: Annotated[str, Meta(min_length=1)] | None = None
    published: bool | None = None
    tags: list[str] | None = None


class CommentSchema(Schema):
    """Schema for Comment model"""

    id: int
    post_id: int
    author_name: str
    content: str
    created_at: datetime
    rating: int


class CommentCreateSchema(Schema):
    """Schema for creating comments"""

    author_name: Annotated[str, Meta(min_length=1, max_length=100)]
    content: Annotated[str, Meta(min_length=1)]
    rating: Annotated[int, Meta(ge=0, le=5)] = 0


class ErrorSchema(Schema):
    """Example error response schema"""

    error: str
    details: str | None = None


class PaginatedResponse(Schema):
    """Generic paginated response"""

    count: int
    next: str | None
    previous: str | None
    results: list[dict]
